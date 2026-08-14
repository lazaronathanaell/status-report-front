from __future__ import annotations

import json
import os
import re
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from . import prompts
from .evaluation import evaluate_ground_truth, validate_process_documents
from .extraction import (
    employee_name_if_present,
    extract_hybrid_pdf,
    format_financial_page_1,
    format_financial_page_2,
    reduce_diploma_context,
    reduce_doe_context,
)
from .structure import structure_data


ROUTES = {
    "portaria": ("PORTARIA", prompts.PORTARIA_PROMPT),
    "oficio": ("OFICIO", prompts.OFICIO_PROMPT),
    "declaracao_orcamentaria": ("DECLARACAO", prompts.DECLARACAO_PROMPT),
    "declaracao_orcamentaria_ano_anterior": ("DECLARACAO", prompts.DECLARACAO_ANO_ANTERIOR_PROMPT),
    "parecer_cepro": ("PARECER_CEPRO", prompts.PARECER_CEPRO),
    "doe": ("DOE", prompts.DOE_PROMPT),
    "declaracao_conclusao_curso": ("DECLARACAO_CONCLUSAO_CURSO", prompts.DECLARACAO_CONCLUSAO_CURSO_PROMPT),
    "diploma": ("DIPLOMA", prompts.DIPLOMA_PROMPT),
}
ALIASES = {
    "declaracao": "declaracao_orcamentaria",
    "declaracao_conclusao": "declaracao_conclusao_curso",
    "declaracao_conclusao_imagem": "declaracao_conclusao_curso",
    "doe_imagem": "doe",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def wait_for_monitor(results_dir: Path, timeout_seconds: float = 30) -> None:
    ready = results_dir / "monitor_ready.json"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            if time.time() - ready.stat().st_mtime < timeout_seconds:
                return
        except FileNotFoundError:
            pass
        time.sleep(0.2)
    raise TimeoutError("O monitor de recursos não confirmou que está pronto")


def document_key(path: Path) -> str:
    key = re.sub(r"[^a-z0-9_]+", "_", path.stem.lower()).strip("_")
    return ALIASES.get(key, key)


def process_id(path: Path) -> str:
    return os.getenv("PROCESS_ID") or next((part for part in reversed(path.parts) if part.isdigit()), path.parent.name)


def load_profile() -> dict[str, Any]:
    profile_path = Path(os.getenv("CASE_PROFILE", "/benchmark/cases/22001149961202519.json"))
    if not profile_path.exists():
        return {"process_id": os.getenv("PROCESS_ID", ""), "user": {"full_name": os.getenv("EMPLOYEE_NAME", "")}}
    return json.loads(profile_path.read_text(encoding="utf-8-sig"))


def ollama_generate(prompt: str) -> tuple[dict[str, Any], float]:
    payload: dict[str, Any] = {
        "model": os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        "prompt": prompt,
        "stream": False,
    }
    mode = os.getenv("GENERATION_MODE", "original").lower()
    if mode == "controlled":
        payload["format"] = "json"
        payload["options"] = {
            "temperature": float(os.getenv("TEMPERATURE", "0")),
            "seed": int(os.getenv("SEED", "42")),
            "num_ctx": int(os.getenv("NUM_CTX", "8192")),
        }
    keep_alive = os.getenv("OLLAMA_KEEP_ALIVE")
    if keep_alive:
        payload["keep_alive"] = keep_alive
    started = time.perf_counter()
    response = requests.post(
        f"{os.getenv('OLLAMA_URL', 'http://ollama:11434').rstrip('/')}/api/generate",
        json=payload,
        timeout=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "900")),
    )
    response.raise_for_status()
    return response.json(), time.perf_counter() - started


def parse_json_response(raw: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError("O modelo não retornou um objeto JSON")
    result = json.loads(match.group(0))
    if isinstance(result, list) and result:
        result = result[0]
    if not isinstance(result, dict):
        raise ValueError("O JSON retornado não é um objeto")
    return result


def model_call(prompt: str, context: str, document_type: str, employee_override: str | None = None) -> tuple[dict, dict]:
    response, elapsed = ollama_generate(prompt + "\n\n" + context)
    raw = parse_json_response(response.get("response", ""))
    if employee_override is not None:
        raw["nome_servidor"] = employee_override
    generated = structure_data(raw, document_type)
    stats = {
        "inference_seconds": elapsed,
        "prompt_eval_count": response.get("prompt_eval_count"),
        "eval_count": response.get("eval_count"),
        "prompt_eval_duration_ns": response.get("prompt_eval_duration"),
        "eval_duration_ns": response.get("eval_duration"),
        "load_duration_ns": response.get("load_duration"),
    }
    return generated, stats


def run_route(key: str, pdf_bytes: bytes, extracted_text: str, statuses: list[dict], employee_name: str) -> tuple[dict, list[dict], dict]:
    diagnostics: dict[str, Any] = {"pipeline_route": key}
    if key == "doe":
        first_type = statuses[0].get("type", "") if statuses else ""
        reduced = reduce_doe_context(extracted_text, employee_name, first_type)
        diagnostics.update({"context_strategy": "original_reduced_around_employee", "model_context_characters": len(reduced), "model_context": reduced})
        result, call = model_call(prompts.DOE_PROMPT, reduced, "DOE")
        return result, [call], diagnostics

    if key == "diploma":
        diploma_mode = os.getenv("DIPLOMA_PREPROCESS_MODE", "original").lower()
        reduced = reduce_diploma_context(extracted_text, employee_name)
        model_context = reduced if diploma_mode == "benchmark_slms" else extracted_text
        diagnostics.update({
            "context_strategy": (
                "benchmark_slms_diploma_employee_and_validation"
                if diploma_mode == "benchmark_slms"
                else "original_full_extracted_text"
            ),
            "diploma_preprocess_mode": diploma_mode,
            "model_context_characters": len(model_context),
            "reduced_context_characters": len(reduced),
        })
        result, call = model_call(prompts.DIPLOMA_PROMPT, model_context, "DIPLOMA")
        return result, [call], diagnostics

    if key == "parecer_asjur":
        # Replica literalmente a seleção da task original, inclusive o `[:-1]`.
        pages = extracted_text.split("\f")[:-1]
        if not pages:
            pages = extracted_text.split("\f")
        first = pages[0] if pages else ""
        final_pages = pages[-2:] if len(pages) > 3 else pages[1:]
        first_result, first_call = model_call(prompts.PARECER_ASJUR_PAG_01_PROMPT + "\n\n" + first, "", "PARECER_ASJUR_01")
        final_prompt = prompts.PARECER_ASJUR_PAGS_FINAIS_PROMPT + "".join(f"\n\n{page}" for page in final_pages)
        final_result, final_call = model_call(final_prompt, "", "PARECER_ASJUR_PAGS_FINAIS")
        first_result.update(final_result)
        diagnostics.update({"context_strategy": "original_first_and_final_pages", "selected_page_count": 1 + len(final_pages)})
        return first_result, [first_call, final_call], diagnostics

    if key == "repercussao_financeira_pg_01":
        table = format_financial_page_1(pdf_bytes, [1])
        result, call = model_call(prompts.REPERCUSSAO_FINANCEIRA_TABLE_01_PROMPT + "\n\n" + table, "", "REPERCUSSAO_FINANCEIRA_TABLE_01_PROMPT")
        diagnostics.update({"context_strategy": "original_pymupdf_table_page_1", "model_context_characters": len(table), "table_text": table})
        return result, [call], diagnostics

    if key == "repercussao_financeira_pg_02":
        # O corpus separou a página 2 original em um PDF de uma página; por isso o índice local é 1.
        table = format_financial_page_2(pdf_bytes, [1])
        found_name = employee_name_if_present(extracted_text, employee_name)
        result, call = model_call(prompts.REPERCUSSAO_FINANCEIRA_TABLE_02_PROMPT + "\n\n" + table, "", "REPERCUSSAO_FINANCEIRA_TABLE_02_PROMPT", found_name)
        diagnostics.update({"context_strategy": "original_pymupdf_table_page_2", "model_context_characters": len(table), "employee_override": found_name, "table_text": table})
        return result, [call], diagnostics

    if key not in ROUTES:
        raise ValueError(f"Rota desconhecida: {key}")
    doc_type, prompt = ROUTES[key]
    result, call = model_call(prompt, extracted_text, doc_type)
    diagnostics.update({"context_strategy": "original_full_extracted_text", "model_context_characters": len(extracted_text)})
    return result, [call], diagnostics


def find_reference(reference_dir: Path, pdf_path: Path, key: str) -> Path | None:
    candidates = list(reference_dir.rglob(f"{key}.json"))
    return min(candidates, key=lambda item: len(item.parts)) if candidates else None


def adapt_reference(reference: Any, generated: Any, key: str) -> tuple[Any, str]:
    if not isinstance(reference, dict):
        return reference, "full"
    if isinstance(reference.get("structured_text"), dict):
        return reference["structured_text"], "full"
    metadata = reference.get("metadata")
    if not isinstance(metadata, dict) or not isinstance(generated, dict):
        return reference, "full"
    partial: dict[str, Any] = {}
    for field in ("nome_servidor", "matricula", "titulacao_atual", "titulacao_almejada"):
        if field in generated and metadata.get(field) is not None:
            partial[field] = metadata[field]
    if "titulacao" in generated and metadata.get("titulacao_almejada") is not None:
        partial["titulacao"] = metadata["titulacao_almejada"]
    if key == "portaria" and "vigencia_promocao" in generated and metadata.get("data") is not None:
        partial["vigencia_promocao"] = metadata["data"]
    if "nup" in generated and reference.get("nup") is not None:
        partial["nup"] = reference["nup"]
    return partial, "metadata_partial"


def evaluate(generated: dict, reference_path: Path | None, key: str) -> dict:
    if reference_path is None:
        return {"reference_found": False, "matched": 0, "compared": 0, "field_accuracy": None, "fields": []}
    reference = json.loads(reference_path.read_text(encoding="utf-8-sig"))
    expected, scope = adapt_reference(reference, generated, key)
    result = evaluate_ground_truth(generated, expected)
    result.update({"reference_file": str(reference_path), "reference_scope": scope, "reference_found": True})
    return result


def main() -> int:
    input_dir = Path(os.getenv("INPUT_DIR", "/data/input"))
    reference_dir = Path(os.getenv("REFERENCE_DIR", "/data/reference"))
    results_dir = Path(os.getenv("RESULTS_DIR", "/results"))
    model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
    profile = load_profile()
    employee_name = str(profile.get("user", {}).get("full_name", ""))
    results_dir.mkdir(parents=True, exist_ok=True)
    wait_for_monitor(results_dir)
    run_id = datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + re.sub(r"[^a-zA-Z0-9_.-]", "_", model)
    run_dir = results_dir / run_id
    run_dir.mkdir()
    state_path = results_dir / "current_run.json"
    records_path = run_dir / "documents.jsonl"
    files = [path for path in sorted(input_dir.rglob("*.pdf")) if document_key(path) in ROUTES or document_key(path).startswith("parecer_asjur") or document_key(path).startswith("repercussao_financeira_pg_")]
    maximum = int(os.getenv("MAX_FILES", "0"))
    if maximum:
        files = files[:maximum]
    state = {
        "run_id": run_id,
        "run_group_id": os.getenv("RUN_GROUP_ID"),
        "model": model,
        "process_id": str(profile.get("process_id") or os.getenv("PROCESS_ID", "")),
        "matrix_model_index": os.getenv("MATRIX_MODEL_INDEX"),
        "matrix_process_index": os.getenv("MATRIX_PROCESS_INDEX"),
        "status": "running",
        "started_at": utc_now(),
        "current_file": None,
    }
    atomic_json(state_path, state)
    records: list[dict] = []

    for index, pdf_path in enumerate(files, 1):
        key = document_key(pdf_path)
        state.update({"current_file": str(pdf_path.relative_to(input_dir)), "file_index": index, "file_count": len(files)})
        atomic_json(state_path, state)
        record: dict[str, Any] = {"file": state["current_file"], "process_id": process_id(pdf_path), "document_type": key, "model": model}
        try:
            started = time.perf_counter()
            pdf_bytes = pdf_path.read_bytes()
            if key == "diploma" and os.getenv("DIPLOMA_PREPROCESS_MODE", "original").lower() == "benchmark_slms":
                extracted, statuses = extract_hybrid_pdf(
                    pdf_bytes,
                    max_pages=1,
                    force_ocr=True,
                    include_native_with_ocr=True,
                )
            else:
                extracted, statuses = extract_hybrid_pdf(pdf_bytes)
            record.update({"input_characters": len(extracted), "ocr_pages": sum(item.get("type") == "Imagem" for item in statuses), "page_statuses": statuses, "extraction_seconds": time.perf_counter() - started})
            if not extracted.strip():
                raise ValueError("PDF sem texto após extração/OCR")
            generated, calls, diagnostics = run_route(key, pdf_bytes, extracted, statuses, employee_name)
            reference_path = find_reference(reference_dir, pdf_path, key)
            eval_count = sum(item.get("eval_count") or 0 for item in calls)
            eval_duration = sum(item.get("eval_duration_ns") or 0 for item in calls)
            record.update({"status": "ok", "generated": generated, "pipeline": diagnostics, "model_calls": calls, "inference_seconds": sum(item["inference_seconds"] for item in calls), "eval_count": eval_count, "eval_duration_ns": eval_duration, "tokens_per_second": eval_count / (eval_duration / 1e9) if eval_duration else None, "evaluation": evaluate(generated, reference_path, key)})
        except Exception as exc:
            record.update({"status": "error", "error": str(exc), "traceback": traceback.format_exc()})
        records.append(record)
        with records_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")

    successful = [item for item in records if item.get("status") == "ok"]
    compared = sum(item["evaluation"]["compared"] for item in successful)
    matched = sum(item["evaluation"]["matched"] for item in successful)
    process_results = {str(profile.get("process_id") or os.getenv("PROCESS_ID", "unknown")): validate_process_documents(records)}
    atomic_json(run_dir / "cross_validation.json", process_results)
    cross = next(iter(process_results.values()))
    measured_rates = [item["tokens_per_second"] for item in successful if item.get("tokens_per_second") is not None]
    summary = {
        "run_id": run_id, "model": model, "pipeline_mode": "original-compatible", "generation_mode": os.getenv("GENERATION_MODE", "original"),
        "started_at": state["started_at"], "finished_at": utc_now(), "files_discovered": len(files), "successful": len(successful), "failed": len(records) - len(successful),
        "field_accuracy": matched / compared if compared else None, "matched_fields": matched, "compared_fields": compared,
        "cross_document_accuracy": cross["cross_document_accuracy"], "cross_document_passed_rules": cross["passed_rules"], "cross_document_applicable_rules": cross["applicable_rules"],
        "mean_inference_seconds": sum(item["inference_seconds"] for item in successful) / len(successful) if successful else None,
        "mean_tokens_per_second": sum(measured_rates) / len(measured_rates) if measured_rates else None,
        "profile": profile,
        "matrix": {
            "run_group_id": os.getenv("RUN_GROUP_ID"),
            "model_index": os.getenv("MATRIX_MODEL_INDEX"),
            "process_index": os.getenv("MATRIX_PROCESS_INDEX"),
        },
    }
    atomic_json(run_dir / "summary.json", summary)
    state.update({"status": "complete", "finished_at": summary["finished_at"], "current_file": None, "run_dir": str(run_dir)})
    atomic_json(state_path, state)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
