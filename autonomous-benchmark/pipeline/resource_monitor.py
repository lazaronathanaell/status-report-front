from __future__ import annotations

import csv
import json
import os
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any

import docker


FIELDS = [
    "run_id", "run_group_id", "model", "process_id",
    "matrix_model_index", "matrix_process_index",
    "timestamp_unix", "elapsed_seconds", "current_file", "file_index", "file_count",
    "ollama_cpu_percent", "ollama_ram_used_bytes", "ollama_ram_limit_bytes",
    "ollama_ram_percent", "runner_cpu_percent", "runner_ram_used_bytes",
    "runner_ram_limit_bytes", "runner_ram_percent",
    "gpu_index", "gpu_utilization_percent", "vram_used_mib", "vram_total_mib", "vram_percent",
    "gpu_power_watts", "gpu_temperature_c",
]


def read_state(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, PermissionError):
        return None


def container_stats(container: Any) -> dict[str, float | None]:
    try:
        stats = container.stats(stream=False, one_shot=True)
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"].get("system_cpu_usage", 0) - stats["precpu_stats"].get("system_cpu_usage", 0)
        online_cpus = stats["cpu_stats"].get("online_cpus") or len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [])) or 1
        cpu_percent = (cpu_delta / system_delta) * online_cpus * 100 if system_delta > 0 else 0.0
        memory = stats.get("memory_stats", {})
        cache = memory.get("stats", {}).get("inactive_file", 0)
        used = max(0, memory.get("usage", 0) - cache)
        limit = memory.get("limit", 0)
        return {"cpu": cpu_percent, "ram": used, "limit": limit}
    except Exception:
        return {"cpu": None, "ram": None, "limit": None}


def gpu_stats() -> list[dict[str, Any]]:
    command = [
        "nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        output = subprocess.run(command, capture_output=True, text=True, timeout=5, check=True).stdout
        result = []
        for line in output.splitlines():
            values = [item.strip() for item in line.split(",")]
            if len(values) == 6:
                result.append(dict(zip(("index", "util", "used", "total", "power", "temp"), values)))
        return result
    except (FileNotFoundError, subprocess.SubprocessError):
        return []


def numeric(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def aggregate(rows: list[dict[str, Any]], key: str) -> dict[str, float | None]:
    values = [numeric(row.get(key)) for row in rows]
    values = [value for value in values if value is not None]
    return {
        "mean": statistics.fmean(values) if values else None,
        "max": max(values) if values else None,
        "p95": sorted(values)[min(len(values) - 1, int(0.95 * len(values)))] if values else None,
    }


def main() -> None:
    results_dir = Path(os.getenv("RESULTS_DIR", "/results"))
    state_path = results_dir / "current_run.json"
    interval = float(os.getenv("SAMPLE_INTERVAL_SECONDS", "1"))
    client = docker.from_env()
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "monitor_ready.json").write_text(
        json.dumps({"ready_at_unix": time.time()}), encoding="utf-8"
    )
    initial_mtime = state_path.stat().st_mtime_ns if state_path.exists() else 0
    state = None
    while state is None or state_path.stat().st_mtime_ns == initial_mtime:
        time.sleep(0.2)
        state = read_state(state_path)
    run_dir = results_dir / state["run_id"]
    csv_path = run_dir / "resources.csv"
    rows: list[dict[str, Any]] = []
    started = time.monotonic()

    with csv_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDS)
        writer.writeheader()
        while True:
            state = read_state(state_path) or state
            try:
                ollama = container_stats(client.containers.get(os.getenv("OLLAMA_CONTAINER", "ollama-experiment")))
            except docker.errors.NotFound:
                ollama = {"cpu": None, "ram": None, "limit": None}
            try:
                runner = container_stats(client.containers.get(os.getenv("RUNNER_CONTAINER", "ollama-benchmark")))
            except docker.errors.NotFound:
                runner = {"cpu": None, "ram": None, "limit": None}
            gpus = gpu_stats() or [{"index": None, "util": None, "used": None, "total": None, "power": None, "temp": None}]
            for gpu in gpus:
                row = {
                    "run_id": state.get("run_id"),
                    "run_group_id": state.get("run_group_id"),
                    "model": state.get("model"),
                    "process_id": state.get("process_id"),
                    "matrix_model_index": state.get("matrix_model_index"),
                    "matrix_process_index": state.get("matrix_process_index"),
                    "timestamp_unix": time.time(), "elapsed_seconds": time.monotonic() - started,
                    "current_file": state.get("current_file"), "file_index": state.get("file_index"),
                    "file_count": state.get("file_count"),
                    "ollama_cpu_percent": ollama["cpu"], "ollama_ram_used_bytes": ollama["ram"],
                    "ollama_ram_limit_bytes": ollama["limit"],
                    "ollama_ram_percent": (100 * ollama["ram"] / ollama["limit"]) if ollama["ram"] is not None and ollama["limit"] else None,
                    "runner_cpu_percent": runner["cpu"], "runner_ram_used_bytes": runner["ram"],
                    "runner_ram_limit_bytes": runner["limit"],
                    "runner_ram_percent": (100 * runner["ram"] / runner["limit"]) if runner["ram"] is not None and runner["limit"] else None,
                    "gpu_index": gpu["index"], "gpu_utilization_percent": gpu["util"],
                    "vram_used_mib": gpu["used"], "vram_total_mib": gpu["total"],
                    "vram_percent": (100 * numeric(gpu["used"]) / numeric(gpu["total"])) if numeric(gpu["used"]) is not None and numeric(gpu["total"]) else None,
                    "gpu_power_watts": gpu["power"], "gpu_temperature_c": gpu["temp"],
                }
                writer.writerow(row)
                rows.append(row)
            output.flush()
            if state.get("status") in {"complete", "failed"}:
                break
            time.sleep(interval)

    summary = {
        "run_id": state.get("run_id"),
        "run_group_id": state.get("run_group_id"),
        "model": state.get("model"),
        "process_id": state.get("process_id"),
        "matrix_model_index": state.get("matrix_model_index"),
        "matrix_process_index": state.get("matrix_process_index"),
        "samples": len(rows),
        "sample_interval_requested_seconds": interval,
        "sample_interval_actual_seconds": aggregate(
            [
                {"delta": float(current["timestamp_unix"]) - float(previous["timestamp_unix"])}
                for previous, current in zip(rows, rows[1:])
            ],
            "delta",
        ),
        "ollama_cpu_percent": aggregate(rows, "ollama_cpu_percent"),
        "ollama_ram_used_bytes": aggregate(rows, "ollama_ram_used_bytes"),
        "ollama_ram_limit_bytes": aggregate(rows, "ollama_ram_limit_bytes"),
        "ollama_ram_percent": aggregate(rows, "ollama_ram_percent"),
        "runner_cpu_percent": aggregate(rows, "runner_cpu_percent"),
        "runner_ram_used_bytes": aggregate(rows, "runner_ram_used_bytes"),
        "runner_ram_limit_bytes": aggregate(rows, "runner_ram_limit_bytes"),
        "runner_ram_percent": aggregate(rows, "runner_ram_percent"),
        "gpu_utilization_percent": aggregate(rows, "gpu_utilization_percent"),
        "vram_used_mib": aggregate(rows, "vram_used_mib"),
        "vram_total_mib": aggregate(rows, "vram_total_mib"),
        "vram_percent": aggregate(rows, "vram_percent"),
        "gpu_power_watts": aggregate(rows, "gpu_power_watts"),
        "gpu_temperature_c": aggregate(rows, "gpu_temperature_c"),
    }
    (run_dir / "resources_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
