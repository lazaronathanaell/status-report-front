from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from typing import Any


MISSING = object()
IGNORED_KEYS = {"id", "documento", "documento_validado", "assinatura_validada"}
LIST_IDENTIFIERS = ("ano", "numero", "codigo", "matricula")
NAME_THRESHOLD = float(os.getenv("NAME_SIMILARITY_THRESHOLD", "0.80"))
TEXT_THRESHOLD = float(os.getenv("TEXT_SIMILARITY_THRESHOLD", "0.80"))
DATE_FIELDS = {
    "data", "data_loa", "data_portaria", "data_assinatura", "data_declaracao",
    "data_estabilidade", "data_inicio", "vigencia_promocao",
}
FUZZY_TEXT_FIELDS = {"assunto"}
NUMERIC_FIELDS = {"repercussao", "contribuicao_patronal", "total", "patronal", "exercicio"}


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).strip().casefold()
    return re.sub(r"\s+", " ", text)


def normalize_identifier(value: Any) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", str(value)).casefold()


def parse_decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    text = str(value).replace("R$", "").replace("\xa0", "").replace(" ", "").strip()
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_strict_date(value: Any) -> datetime | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        return None
    try:
        return datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        return None


def field_name(path: str) -> str:
    clean = re.sub(r"\[[^]]+\]", "", path)
    return clean.rsplit(".", 1)[-1]


def metric_for(path: str, expected: Any) -> str:
    name = field_name(path)
    if name in DATE_FIELDS or name.startswith("data_"):
        return "date_exact_dd_mm_yyyy"
    if "nome" in name or name in {"assinante", "ordenador"}:
        return "sequence_matcher"
    if name in FUZZY_TEXT_FIELDS:
        return "sequence_matcher"
    if isinstance(expected, bool):
        return "boolean_exact"
    if isinstance(expected, (int, float, Decimal)) or name in NUMERIC_FIELDS:
        return "numeric_tolerance"
    return "normalized_exact"


def compare_scalar(path: str, expected: Any, actual: Any) -> dict[str, Any]:
    metric = metric_for(path, expected)
    missing = actual is MISSING
    score = 0.0
    threshold = 1.0

    if not missing and metric == "date_exact_dd_mm_yyyy":
        expected_date = parse_strict_date(expected)
        actual_date = parse_strict_date(actual)
        correct = expected_date is not None and actual_date is not None and expected == actual
        score = 1.0 if correct else 0.0
    elif not missing and metric == "sequence_matcher":
        threshold = NAME_THRESHOLD if "nome" in field_name(path) else TEXT_THRESHOLD
        score = SequenceMatcher(None, normalize_text(expected), normalize_text(actual)).ratio()
        correct = score >= threshold
    elif not missing and metric == "boolean_exact":
        correct = type(actual) is bool and actual is expected
        score = 1.0 if correct else 0.0
    elif not missing and metric == "numeric_tolerance":
        expected_number = parse_decimal(expected)
        actual_number = parse_decimal(actual)
        tolerance = Decimal("0") if isinstance(expected, int) else Decimal("0.01")
        correct = expected_number is not None and actual_number is not None and abs(expected_number - actual_number) <= tolerance
        score = 1.0 if correct else 0.0
    elif not missing:
        actual_values = actual if isinstance(actual, list) else [actual]
        correct = normalize_identifier(expected) in {normalize_identifier(item) for item in actual_values}
        score = 1.0 if correct else 0.0
    else:
        correct = False

    return {
        "path": path,
        "metric": metric,
        "threshold": threshold,
        "score": score,
        "correct": correct,
        "missing": missing,
        "expected": expected,
        "actual": None if missing else actual,
    }


def list_identifier(expected: list[Any], actual: Any) -> str | None:
    if not expected or not all(isinstance(item, dict) for item in expected) or not isinstance(actual, list):
        return None
    for key in LIST_IDENTIFIERS:
        if all(key in item for item in expected):
            return key
    return None


def compare_node(expected: Any, actual: Any, path: str, fields: list[dict[str, Any]]) -> None:
    if isinstance(expected, dict):
        actual_dict = actual if isinstance(actual, dict) else {}
        for key, child in expected.items():
            if key in IGNORED_KEYS:
                continue
            child_path = f"{path}.{key}" if path else key
            compare_node(child, actual_dict.get(key, MISSING), child_path, fields)
        return
    if isinstance(expected, list):
        actual_list = actual if isinstance(actual, list) else ([] if actual is MISSING else [actual])
        identifier = list_identifier(expected, actual_list)
        if identifier:
            indexed = {normalize_identifier(item.get(identifier)): item for item in actual_list if isinstance(item, dict)}
            for item in expected:
                identity = normalize_identifier(item.get(identifier))
                compare_node(item, indexed.get(identity, MISSING), f"{path}[{identifier}={item.get(identifier)}]", fields)
        else:
            for index, item in enumerate(expected):
                compare_node(item, actual_list[index] if index < len(actual_list) else MISSING, f"{path}[{index}]", fields)
        return
    fields.append(compare_scalar(path, expected, actual))


def all_paths(value: Any, path: str = "") -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key not in IGNORED_KEYS:
                result |= all_paths(child, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        identifier = next((key for key in LIST_IDENTIFIERS if value and all(isinstance(item, dict) and key in item for item in value)), None)
        for index, child in enumerate(value):
            label = f"{identifier}={child[identifier]}" if identifier else str(index)
            result |= all_paths(child, f"{path}[{label}]")
    else:
        result.add(path)
    return result


def evaluate_ground_truth(generated: Any, reference: Any) -> dict[str, Any]:
    if isinstance(reference, dict):
        reference = reference.get("structured_text", reference)
    fields: list[dict[str, Any]] = []
    compare_node(reference, generated, "", fields)
    matched = sum(field["correct"] for field in fields)
    expected_paths = all_paths(reference)
    actual_paths = all_paths(generated)
    return {
        "reference_found": True,
        "matched": matched,
        "compared": len(fields),
        "field_accuracy": matched / len(fields) if fields else None,
        "missing_fields": [field["path"] for field in fields if field["missing"]],
        "extra_fields": sorted(actual_paths - expected_paths),
        "fields": fields,
    }


def get_path(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return MISSING
        current = current[part]
    return current


def cross_comparison(rule: str, left_doc: str, left_value: Any, right_doc: str, right_value: Any, field: str) -> dict[str, Any]:
    comparison = compare_scalar(field, left_value, right_value) if left_value is not MISSING else compare_scalar(field, None, MISSING)
    return {
        "rule": rule, "left_document": left_doc, "right_document": right_doc,
        "left_value": None if left_value is MISSING else left_value,
        "right_value": None if right_value is MISSING else right_value,
        "metric": comparison["metric"], "score": comparison["score"],
        "threshold": comparison["threshold"], "correct": comparison["correct"],
    }


def validate_process_documents(records: list[dict[str, Any]]) -> dict[str, Any]:
    documents: dict[str, dict[str, Any]] = {}
    for record in records:
        if record.get("status") != "ok" or not isinstance(record.get("generated"), dict):
            continue
        doc_type = record["document_type"]
        if doc_type.startswith("repercussao_financeira"):
            doc_type = "repercussao_financeira"
        documents.setdefault(doc_type, {}).update(record["generated"])

    rules: list[dict[str, Any]] = []

    def compare_if_present(rule: str, left_doc: str, left_path: str, right_doc: str, right_path: str, metric_field: str | None = None) -> None:
        if left_doc not in documents or right_doc not in documents:
            return
        left_value = get_path(documents[left_doc], left_path)
        right_value = get_path(documents[right_doc], right_path)
        # Não penaliza um documento por um campo que não faz parte do seu contrato
        # original (por exemplo, DIPLOMA não possui matrícula).
        if left_value is MISSING or right_value is MISSING:
            return
        rules.append(cross_comparison(
            rule, left_doc, left_value,
            right_doc, right_value, metric_field or left_path,
        ))

    for other in ("oficio", "doe", "parecer_cepro", "parecer_asjur", "declaracao_conclusao_curso", "diploma", "repercussao_financeira"):
        compare_if_present(f"nome_servidor:portaria={other}", "portaria", "nome_servidor", other, "nome_servidor", "nome_servidor")
        compare_if_present(f"matricula:portaria={other}", "portaria", "matricula", other, "matricula", "matricula")

    compare_if_present("numero_portaria:portaria=oficio", "portaria", "numero_portaria", "oficio", "numero_portaria")
    for declaration in ("declaracao_orcamentaria", "declaracao_orcamentaria_ano_anterior"):
        compare_if_present(f"nup:portaria={declaration}", "portaria", "nup", declaration, "nup", "nup")
    compare_if_present("titulacao:portaria=parecer_cepro", "portaria", "titulacao_almejada", "parecer_cepro", "titulacao_almejada")
    compare_if_present("titulacao:portaria=declaracao_conclusao", "portaria", "titulacao_almejada", "declaracao_conclusao_curso", "titulacao")
    compare_if_present("titulacao:portaria=diploma", "portaria", "titulacao_almejada", "diploma", "titulacao")
    compare_if_present("assinante=secretario:portaria", "portaria", "nome_secretario_educacao", "portaria", "nome_assinante_documento", "nome_servidor")
    compare_if_present("assinante=ordenador:declaracao", "declaracao_orcamentaria", "nome_ordenador_despesas", "declaracao_orcamentaria", "nome_assinante_documento", "nome_servidor")

    if "portaria" in documents and "doe" in documents:
        vigencia = get_path(documents["portaria"], "vigencia_promocao")
        estabilidade = get_path(documents["doe"], "data_estabilidade")
        vigencia_date = parse_strict_date(vigencia)
        estabilidade_date = parse_strict_date(estabilidade)
        correct = vigencia_date is not None and estabilidade_date is not None and vigencia_date >= estabilidade_date
        rules.append({
            "rule": "vigencia_promocao>=data_estabilidade", "left_document": "portaria", "right_document": "doe",
            "left_value": None if vigencia is MISSING else vigencia, "right_value": None if estabilidade is MISSING else estabilidade,
            "metric": "date_order_dd_mm_yyyy", "score": 1.0 if correct else 0.0, "threshold": 1.0, "correct": correct,
        })

    if "parecer_cepro" in documents and documents["parecer_cepro"].get("diploma_em_confeccao") is True:
        correct = "declaracao_conclusao_curso" in documents
        rules.append({
            "rule": "diploma_em_confeccao_requer_declaracao_conclusao", "left_document": "parecer_cepro",
            "right_document": "declaracao_conclusao_curso", "left_value": True,
            "right_value": "presente" if correct else "ausente", "metric": "document_presence",
            "score": 1.0 if correct else 0.0, "threshold": 1.0, "correct": correct,
        })

    def by_year(items: Any) -> dict[int, dict[str, Any]]:
        result: dict[int, dict[str, Any]] = {}
        if not isinstance(items, list):
            return result
        for item in items:
            try:
                result[int(item["ano"])] = item
            except (KeyError, TypeError, ValueError):
                continue
        return result

    if "repercussao_financeira" in documents:
        financial = documents["repercussao_financeira"]
        table_1 = by_year(financial.get("tabela_1_valores"))
        table_2 = by_year(financial.get("tabela_2_valores"))
        for year, row_2 in sorted(table_2.items()):
            row_1 = table_1.get(year, {})
            rules.append(cross_comparison(
                f"repercussao[{year}]=total[{year}]", "repercussao_financeira.tabela_1",
                row_1.get("repercussao", MISSING), "repercussao_financeira.tabela_2",
                row_2.get("total", MISSING), "total",
            ))
            rules.append(cross_comparison(
                f"contribuicao_patronal[{year}]=patronal[{year}]", "repercussao_financeira.tabela_1",
                row_1.get("contribuicao_patronal", MISSING), "repercussao_financeira.tabela_2",
                row_2.get("patronal", MISSING), "patronal",
            ))

        for declaration in ("declaracao_orcamentaria", "declaracao_orcamentaria_ano_anterior"):
            if declaration not in documents:
                continue
            declaration_values = by_year(documents[declaration].get("repercussao_financeira"))
            for year, declaration_row in sorted(declaration_values.items()):
                row_1 = table_1.get(year, {})
                rules.append(cross_comparison(
                    f"declaracao.exercicio[{year}]=repercussao[{year}]", declaration,
                    declaration_row.get("exercicio", MISSING), "repercussao_financeira.tabela_1",
                    row_1.get("repercussao", MISSING), "exercicio",
                ))
                rules.append(cross_comparison(
                    f"declaracao.patronal[{year}]=contribuicao_patronal[{year}]", declaration,
                    declaration_row.get("patronal", MISSING), "repercussao_financeira.tabela_1",
                    row_1.get("contribuicao_patronal", MISSING), "patronal",
                ))

    correct_count = sum(rule["correct"] for rule in rules)
    return {
        "applicable_rules": len(rules), "passed_rules": correct_count,
        "cross_document_accuracy": correct_count / len(rules) if rules else None,
        "rules": rules,
    }
