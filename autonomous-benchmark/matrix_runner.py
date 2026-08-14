from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


BENCH_DIR = Path(__file__).resolve().parent


def compose_command() -> list[str]:
    docker = shutil.which("docker")
    if docker:
        probe = subprocess.run([docker, "compose", "version"], capture_output=True, text=True)
        if probe.returncode == 0:
            return [docker, "compose"]
    legacy = shutil.which("docker-compose")
    if legacy:
        return [legacy]
    raise RuntimeError("Docker Compose não foi encontrado")


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (BENCH_DIR / path).resolve()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def run(command: list[str], env: dict[str, str], check: bool = True, timeout: int | None = None) -> int:
    print("+", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=BENCH_DIR, env=env, timeout=timeout)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command)
    return result.returncode


def validate_matrix(matrix: dict[str, Any]) -> None:
    models = matrix.get("models")
    cases = matrix.get("processes")
    if not isinstance(models, list) or not models or not all(isinstance(item, str) and item for item in models):
        raise ValueError("`models` deve ser uma lista não vazia")
    if not isinstance(cases, list) or not cases:
        raise ValueError("`processes` deve ser uma lista não vazia")
    identifiers: set[str] = set()
    for case in cases:
        process_id = str(case.get("process_id", ""))
        if not process_id or process_id in identifiers:
            raise ValueError(f"Processo ausente ou duplicado: {process_id!r}")
        identifiers.add(process_id)
        for field in ("input_dir", "reference_dir", "profile"):
            path = resolve_path(str(case.get(field, "")))
            if not path.exists():
                raise FileNotFoundError(f"{process_id}: `{field}` não encontrado: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa modelos x processos sequencialmente")
    parser.add_argument("--matrix", default="matrix.json")
    parser.add_argument("--env-file", default="configs/example.env")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    matrix_path = resolve_path(args.matrix)
    env_file = resolve_path(args.env_file)
    matrix = json.loads(matrix_path.read_text(encoding="utf-8-sig"))
    validate_matrix(matrix)
    if not env_file.exists():
        raise FileNotFoundError(env_file)
    if args.validate_only:
        print(json.dumps({
            "valid": True,
            "models": len(matrix["models"]),
            "processes": len(matrix["processes"]),
            "planned_runs": len(matrix["models"]) * len(matrix["processes"]),
        }, ensure_ascii=False, indent=2))
        return 0

    run_group_id = datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + safe_name(matrix.get("name", "matrix"))
    matrix_dir = BENCH_DIR / "results" / "matrices" / run_group_id
    matrix_summary_path = matrix_dir / "summary.json"
    records: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "run_group_id": run_group_id,
        "matrix_file": str(matrix_path),
        "model_order": matrix["models"],
        "process_order": [str(case["process_id"]) for case in matrix["processes"]],
        "status": "running",
        "runs": records,
        "model_cleanup": [],
    }
    write_json(matrix_summary_path, report)

    compose = compose_command() + ["-f", str(BENCH_DIR / "compose.yml"), "--env-file", str(env_file)]
    base_env = os.environ.copy()
    base_env["RUN_GROUP_ID"] = run_group_id
    continue_on_error = bool(matrix.get("continue_on_error", True))
    remove_model_after_group = bool(matrix.get("remove_model_after_group", True))
    model_keep_alive = str(matrix.get("model_keep_alive", "-1"))
    report["model_keep_alive"] = model_keep_alive
    active_model: tuple[str, dict[str, str]] | None = None

    def cleanup_model(model: str, model_env: dict[str, str]) -> None:
        cleanup: dict[str, Any] = {"model": model, "requested": remove_model_after_group}
        if remove_model_after_group:
            # keep_alive=0 libera RAM/VRAM; stop cobre também uma chamada interrompida.
            cleanup["stop_exit_code"] = run(
                compose + ["exec", "-T", "ollama", "ollama", "stop", model],
                model_env,
                check=False,
            )
            cleanup["remove_exit_code"] = run(
                compose + ["exec", "-T", "ollama", "ollama", "rm", model],
                model_env,
                check=False,
            )
            cleanup["removed"] = cleanup["remove_exit_code"] == 0
        else:
            cleanup["removed"] = False
        report["model_cleanup"].append(cleanup)
        write_json(matrix_summary_path, report)

    try:
        run(compose + ["up", "-d", "--build", "--wait", "ollama"], base_env)
        for model_index, model in enumerate(matrix["models"], 1):
            model_env = base_env | {
                "OLLAMA_MODEL": model,
                "OLLAMA_KEEP_ALIVE": model_keep_alive,
                "MATRIX_MODEL_INDEX": str(model_index),
            }
            active_model = (model, model_env)
            print(f"\n=== Modelo {model_index}/{len(matrix['models'])}: {model} ===", flush=True)
            run(compose + ["run", "--rm", "model-pull"], model_env)

            for process_index, case in enumerate(matrix["processes"], 1):
                process_id = str(case["process_id"])
                case_env = model_env | {
                    "PROCESS_ID": process_id,
                    "INPUT_DIR": str(resolve_path(case["input_dir"])),
                    "REFERENCE_DIR": str(resolve_path(case["reference_dir"])),
                    "CASE_PROFILE_HOST": str(resolve_path(case["profile"])),
                    "MATRIX_PROCESS_INDEX": str(process_index),
                }
                print(f"\n--- Processo {process_index}/{len(matrix['processes'])}: {process_id} ---", flush=True)
                run(compose + ["up", "-d", "--build", "--force-recreate", "metrics"], case_env)
                exit_code = run(
                    compose + ["up", "--build", "--no-deps", "--force-recreate", "--exit-code-from", "benchmark", "benchmark"],
                    case_env,
                    check=False,
                )
                try:
                    run(compose + ["wait", "metrics"], case_env, timeout=120)
                except subprocess.TimeoutExpired:
                    run(compose + ["stop", "metrics"], case_env, check=False)

                state_path = BENCH_DIR / "results" / "current_run.json"
                state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
                run_id = state.get("run_id")
                summary_path = BENCH_DIR / "results" / str(run_id) / "summary.json" if run_id else None
                summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path and summary_path.exists() else None
                record = {
                    "model": model,
                    "model_index": model_index,
                    "process_id": process_id,
                    "process_index": process_index,
                    "exit_code": exit_code,
                    "run_id": run_id,
                    "summary_file": str(summary_path) if summary_path else None,
                    "summary": summary,
                }
                records.append(record)
                write_json(matrix_summary_path, report)
                if exit_code != 0 and not continue_on_error:
                    raise RuntimeError(f"Falha em {model}/{process_id}")
            active_model = None
            cleanup_model(model, model_env)
        report["status"] = "complete"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        raise
    finally:
        if active_model is not None:
            cleanup_model(*active_model)
        report["finished_at"] = datetime.now().isoformat()
        write_json(matrix_summary_path, report)
        run(compose + ["down"], base_env, check=False)

    print(json.dumps({"run_group_id": run_group_id, "runs": len(records), "summary": str(matrix_summary_path)}, ensure_ascii=False, indent=2))
    return 0 if all(item["exit_code"] == 0 for item in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
