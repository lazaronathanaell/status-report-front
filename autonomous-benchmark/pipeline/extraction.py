"""Extração local equivalente aos utilitários usados pela aplicação."""

from __future__ import annotations

import logging
import re
import unicodedata
from difflib import SequenceMatcher
from io import BytesIO

import fitz
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image, ImageFilter


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    return "".join(c for c in value if not unicodedata.combining(c)).upper().strip()


def is_page_scanned(page: fitz.Page, text_area_threshold: float = 0.05) -> bool:
    total_page_area = abs(page.rect)
    if total_page_area == 0:
        return True
    text_area = 0.0
    for block in page.get_text("blocks"):
        if str(block[4]).strip():
            text_area += abs(fitz.Rect(block[:4]))
    return (text_area / total_page_area) < text_area_threshold


def detect_rotation_angle(image: Image.Image) -> int:
    try:
        osd = pytesseract.image_to_osd(image)
        line = next((item for item in osd.splitlines() if item.startswith("Rotate:")), None)
        return int(line.split(":", 1)[1].strip()) if line else 0
    except Exception as exc:  # comportamento tolerante da aplicação original
        logging.warning("OSD não detectou rotação: %s", exc)
        return 0


def extract_ocr_from_page(file_bytes: bytes, page_num: int) -> str:
    try:
        images = convert_from_bytes(
            pdf_file=file_bytes,
            dpi=600,
            first_page=page_num + 1,
            last_page=page_num + 1,
            fmt="jpeg",
            thread_count=1,
        )
        if not images:
            return ""
        image = images[0]
        image = image.rotate(-detect_rotation_angle(image), expand=True)
        image = image.filter(ImageFilter.MedianFilter(size=5)).convert("L")
        return pytesseract.image_to_string(image, lang="por").strip()
    except Exception as exc:
        logging.error("OCR falhou na página %s: %s", page_num + 1, exc)
        return ""


def extract_hybrid_pdf(
    file_bytes: bytes,
    max_pages: int | None = None,
    force_ocr: bool = False,
    include_native_with_ocr: bool = False,
) -> tuple[str, list[dict]]:
    texts: list[str] = []
    statuses: list[dict] = []
    with fitz.open(stream=BytesIO(file_bytes), filetype="pdf") as document:
        pages_to_process = min(max_pages, len(document)) if max_pages is not None else len(document)
        for page_num in range(pages_to_process):
            page = document[page_num]
            try:
                scanned = force_ocr or is_page_scanned(page)
                if scanned:
                    ocr_text = extract_ocr_from_page(file_bytes, page_num)
                    native_text = page.get_text().strip()
                    text = f"{native_text}\n{ocr_text}".strip() if include_native_with_ocr else ocr_text
                else:
                    text = page.get_text().strip()
                texts.append(f"{text}\f")
                statuses.append(
                    {"page_num": page_num + 1, "type": "Imagem" if scanned else "Texto Selecionável"}
                )
            except Exception as exc:
                logging.error("Erro na página %s: %s", page_num + 1, exc)
                texts.append(f"ERRO_PAGINA_{page_num + 1}\f")
                statuses.append({"page_num": page_num + 1, "error": str(exc)})
    return "".join(texts).rstrip("\f"), statuses


def reduce_diploma_context(
    context: str,
    employee_name: str,
    lines_above: int = 4,
    lines_below: int = 8,
    minimum_similarity: float = 0.60,
) -> str:
    """Replica o recorte específico usado pelo preprocess do benchmark-slms."""
    normalized_context = normalize_text(context).replace("  ", " ")
    normalized_name = normalize_text(employee_name)
    lines = normalized_context.split("\n")
    best_index: int | None = None
    best_similarity = 0.0

    for index, line in enumerate(lines):
        similarity = SequenceMatcher(None, normalized_name, line.strip()).ratio()
        if similarity >= minimum_similarity and similarity > best_similarity:
            best_index = index
            best_similarity = similarity

    if best_index is None:
        name_parts = normalized_name.split()
        for index, line in enumerate(lines):
            if len(name_parts) >= 2 and all(part in line for part in name_parts[:2]):
                best_index = index
                break

    # O preprocess original volta ao contexto completo quando não encontra o nome.
    if best_index is None:
        return normalized_context

    start = max(0, best_index - lines_above)
    end = min(len(lines), best_index + lines_below + 1)
    employee_excerpt = "\n".join(lines[start:end]).strip()

    validation_pattern = re.compile(r"DOCUMENTO\s+CONFERIDO\s+E\s+VALIDADO\s+POR", re.IGNORECASE)
    validation_index = next((index for index, line in enumerate(lines) if validation_pattern.search(line)), None)
    validation_excerpt = ""
    if validation_index is not None:
        validation_excerpt = "\n".join(lines[validation_index : validation_index + 3]).strip()
    return "\n\n".join(part for part in (employee_excerpt, validation_excerpt) if part) or normalized_context


def reduce_doe_context(
    context: str,
    employee_name: str,
    document_type: str,
    lines_above: int = 3,
    lines_below: int = 2,
) -> str:
    """Replica `extrair_contexto_reduzido`, com fallback seguro para imagem."""
    lines = context.split("\n")
    wanted = employee_name.upper().strip()
    parts = wanted.split()
    strategies = (
        lambda line: wanted in line.upper(),
        lambda line: len(parts) >= 3 and all(part in line.upper() for part in parts[:3]),
        lambda line: len(parts) >= 2 and all(part in line.upper() for part in parts[:2]),
    )
    found_line = None
    found_index = None
    for index, line in enumerate(lines):
        if any(strategy(line) for strategy in strategies):
            found_line, found_index = line, index
            break
    if found_line is None or found_index is None:
        return ""

    stability_pattern = re.compile(
        r"RESOLVE\s+DECLARAR\s+a\s+estabilidade\s+no\s+Serviço\s+Público\s+Estadual",
        flags=re.IGNORECASE,
    )
    stability_line = next(
        (line for line in lines[found_index + 1 :] if stability_pattern.search(line)), ""
    )
    if document_type == "Imagem":
        return "\n".join(part for part in (found_line.strip(), stability_line.strip()) if part)

    if document_type == "Texto Selecionável":
        if stability_line:
            lines_below = 3
        start = max(0, found_index - lines_above)
        end = min(len(lines), found_index + lines_below + 1)
        excerpt = "\n".join(lines[start:end]).strip()
        return f"{excerpt}\n{stability_line.strip()}".strip()
    return found_line.strip()


def employee_name_if_present(context: str, employee_name: str) -> str:
    normalized_context = normalize_text(context.replace("\n", " "))
    return employee_name if normalize_text(employee_name) in normalized_context else ""


def extract_tables(pdf_bytes: bytes, pages: list[int]) -> dict[int, list[list[list[str]]]]:
    result: dict[int, list] = {}
    with fitz.open(stream=BytesIO(pdf_bytes), filetype="pdf") as document:
        for page_number in pages:
            if not 1 <= page_number <= len(document):
                continue
            page = document[page_number - 1]
            result[page_number] = [table.extract() for table in page.find_tables()]
    return result


def format_financial_page_1(pdf_bytes: bytes, pages: list[int]) -> str:
    output: list[str] = []
    for tables in extract_tables(pdf_bytes, pages).values():
        for table in tables:
            if not table:
                continue
            width = max(len(row) for row in table)
            for row in table:
                cells = [str(cell) if cell is not None else "" for cell in row]
                output.append(" | ".join(cells + [""] * (width - len(cells))))
            output.append("")
    return "\n".join(output).strip()


def format_financial_page_2(pdf_bytes: bytes, pages: list[int]) -> str:
    output: list[str] = []
    tables_by_page = extract_tables(pdf_bytes, pages)
    for page_number in pages:
        for table in tables_by_page.get(page_number, []):
            if not table:
                continue
            width = max(len(row) for row in table)
            for row in table[1:]:
                cells = [str(cell) if cell is not None else "" for cell in row]
                cells += [""] * (width - len(cells))
                selected = ([cells[0]] + cells[-2:]) if len(cells) >= 3 else cells
                selected = [value.replace("\n", " ") if i == 0 else value.replace("\n", "") for i, value in enumerate(selected)]
                output.append(" | ".join(selected))
            output.append("")
    return "\n".join(output).strip()
