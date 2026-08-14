"""Pós-processamento compatível com `app/modules/structure.py`."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def _float(value: Any) -> float:
    text = str(value).strip()
    text = text.replace(".", "").replace(",", ".") if "," in text else text.replace(",", "")
    try:
        return float(text)
    except (TypeError, ValueError):
        return 0.0


def _br(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def aggregate_by_year(rows: list[dict]) -> list[dict]:
    result: dict[str, dict] = {}
    for item in rows or []:
        year = str(item.get("ano", ""))
        date_text = str(item.get("data_inicio", ""))
        try:
            date = datetime.strptime(date_text, "%d/%m/%Y")
        except ValueError:
            date = datetime.max
        if year not in result:
            result[year] = {
                "ano": year,
                "data_inicio": date_text,
                "total": _float(item.get("total", 0)),
                "patronal": _float(item.get("patronal", 0)),
                "_date": date,
            }
        else:
            result[year]["total"] += _float(item.get("total", 0))
            result[year]["patronal"] += _float(item.get("patronal", 0))
            if date < result[year]["_date"]:
                result[year]["data_inicio"], result[year]["_date"] = date_text, date
    for data in result.values():
        data["total"], data["patronal"] = _br(data["total"]), _br(data["patronal"])
        data.pop("_date", None)
    return list(result.values())


def structure_data(info: dict, document_type: str) -> dict:
    """Mantém o contrato da aplicação; validações externas ficam explicitamente nulas."""
    valid = {"documento_validado": True, "contexto": ""}
    signatures = None
    fields: dict[str, list[str]] = {
        "PORTARIA": ["nup", "numero_portaria", "nome_servidor", "matricula", "nivel_atual", "titulacao_atual", "nivel_almejado", "titulacao_almejada", "vigencia_promocao", "legislacao", "nome_secretario_educacao", "nome_assinante_documento", "data_portaria", "data_assinatura", "codigo_validacao"],
        "OFICIO": ["numero_oficio", "numero_portaria", "nome_servidor", "matricula"],
        "DECLARACAO": ["nup", "numero_loa", "data_loa", "recursos_suficientes", "repercussao_financeira", "nome_ordenador_despesas", "nome_assinante_documento", "data_declaracao", "data_assinatura", "codigo_validacao"],
        "PARECER_CEPRO": ["nome_servidor", "matricula", "titulacao_almejada", "reconhecimento_curso", "requisitos_exigidos", "diploma_em_confeccao"],
        "DOE": ["nome_servidor", "matricula", "data_estabilidade", "assunto"],
        "DECLARACAO_CONCLUSAO_CURSO": ["nome_servidor", "titulacao", "requisitos_conclusao"],
        "DIPLOMA": ["nome_servidor", "titulacao", "assinatura_eletronica"],
    }
    labels = {
        "PORTARIA": "PORTARIA", "OFICIO": "OFÍCIO",
        "DECLARACAO": "DECLARAÇÃO DE DISPONIBILIDADE ORÇAMENTÁRIA E FINANCEIRA",
        "PARECER_CEPRO": "PARECER SEDUC/CEPRO", "DOE": "DIÁRIO OFICIAL DO ESTADO",
        "DECLARACAO_CONCLUSAO_CURSO": "DECLARAÇÃO DE CONCLUSÃO DE CURSO", "DIPLOMA": "DIPLOMA",
    }
    if document_type in fields:
        output = {"documento": labels[document_type]}
        output.update({key: info.get(key) for key in fields[document_type]})
        if document_type == "PARECER_CEPRO":
            values = output.get("matricula") or []
            if not isinstance(values, list):
                values = [values]
            output["matricula"] = [re.sub(r"[^A-Za-z0-9]", "", str(item)) for item in values]
        if document_type in {"PORTARIA", "DECLARACAO"}:
            output["assinatura_validada"] = signatures
        output["documento_validado"] = valid
        return output

    if document_type == "PARECER_ASJUR_01":
        number = str(info.get("numero_parecer", ""))
        if number.endswith("/SEDUC/ASJUR"):
            number = number.rsplit("/", 2)[0]
        return {"documento": "PARECER_ASJUR", "numero_parecer": number, "nome_servidor": info.get("nome_servidor"), "matricula": info.get("matricula"), "documento_validado": valid}
    if document_type == "PARECER_ASJUR_PAGS_FINAIS":
        return {"cumprimento_exigencias": info.get("cumprimento_exigencias")}
    if document_type == "REPERCUSSAO_FINANCEIRA_TABLE_01_PROMPT":
        return {"documento": "REPERCUSSÃO FINANCEIRA", "tabela_1_valores": info.get("tabela_1_valores"), "documento_validado": valid}
    if document_type == "REPERCUSSAO_FINANCEIRA_TABLE_02_PROMPT":
        return {"matricula": info.get("matricula"), "nome_servidor": info.get("nome_servidor"), "tabela_2_valores": aggregate_by_year(info.get("tabela_2_valores") or [])}
    raise ValueError(f"Tipo não suportado: {document_type}")
