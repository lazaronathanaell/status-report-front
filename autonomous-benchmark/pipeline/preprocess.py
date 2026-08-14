"""Prepara processos a partir de PDFs completos e do index.json do corpus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import fitz


METADATA_KEYS = {
    "nome", "matricula", "data", "titulacao_atual",
    "titulacao_almejada", "parecer_negativo",
}


def page_numbers(value: Any) -> list[int]:
    if isinstance(value, int):
        return [value]
    if not isinstance(value, list) or not value or not all(isinstance(item, int) for item in value):
        raise ValueError(f"Definição de páginas inválida: {value!r}")
    if len(value) == 2 and value[0] < value[1]:
        return list(range(value[0], value[1] + 1))
    return value


def iter_processes(index: dict[str, Any]):
    for group, processes in index.items():
        if not isinstance(processes, dict):
            continue
        for process_id, documents in processes.items():
            if isinstance(documents, dict):
                yield group, str(process_id), documents


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def prepare_process(raw_pdf: Path, output_root: Path, process_id: str, documents: dict[str, Any]) -> dict[str, Any]:
    process_dir = output_root / process_id
    pdf_dir = process_dir / "pdfs"
    truth_dir = process_dir / "ground_truth"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    truth_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "nome_servidor": documents.get("nome", ""),
        "matricula": documents.get("matricula", []),
        "data": documents.get("data", ""),
        "titulacao_atual": documents.get("titulacao_atual", ""),
        "titulacao_almejada": documents.get("titulacao_almejada", ""),
        "parecer_negativo": documents.get("parecer_negativo", False),
    }
    profile = {
        "process_id": process_id,
        "user": {
            "full_name": metadata["nome_servidor"],
            "matriculas": metadata["matricula"],
            "process_date": metadata["data"],
            "titulacao_atual": metadata["titulacao_atual"],
            "titulacao_almejada": metadata["titulacao_almejada"],
        },
    }
    write_json(process_dir / "profile.json", profile)

    generated: list[dict[str, Any]] = []
    with fitz.open(raw_pdf) as source:
        for document_name, definition in documents.items():
            if document_name in METADATA_KEYS:
                continue
            pages = page_numbers(definition)
            invalid = [number for number in pages if number < 1 or number > len(source)]
            if invalid:
                raise IndexError(f"{process_id}/{document_name}: páginas inexistentes {invalid}")
            output_pdf = pdf_dir / f"{document_name}.pdf"
            with fitz.open() as target:
                for number in pages:
                    target.insert_pdf(source, from_page=number - 1, to_page=number - 1)
                target.save(output_pdf)
            reference = {
                "nup": process_id,
                "content_type": document_name,
                "arquivo_original": output_pdf.name,
                "metadata": metadata,
                "reference_scope": "metadata_partial",
            }
            write_json(truth_dir / f"{document_name}.json", reference)
            generated.append({"document": document_name, "pages": pages, "pdf": str(output_pdf)})
    return {"process_id": process_id, "documents": generated, "profile": str(process_dir / "profile.json")}


def main() -> int:
    parser = argparse.ArgumentParser(description="Separa processos descritos no index.json")
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--process", action="append", dest="processes", help="NUP a preparar; repetível")
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding="utf-8-sig"))
    selected = set(args.processes or [])
    manifest: list[dict[str, Any]] = []
    for group, process_id, documents in iter_processes(index):
        if selected and process_id not in selected:
            continue
        raw_pdf = args.raw_dir / f"{process_id}.pdf"
        if not raw_pdf.exists():
            raise FileNotFoundError(f"PDF bruto não encontrado: {raw_pdf}")
        item = prepare_process(raw_pdf, args.output_dir, process_id, documents)
        item["group"] = group
        manifest.append(item)
    if selected - {item["process_id"] for item in manifest}:
        raise KeyError(f"Processos ausentes no índice: {sorted(selected - {item['process_id'] for item in manifest})}")
    write_json(args.output_dir / "preprocess_manifest.json", {"processes": manifest})
    print(json.dumps({"prepared_processes": len(manifest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
