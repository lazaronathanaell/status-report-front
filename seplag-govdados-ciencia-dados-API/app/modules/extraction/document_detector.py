from ..prompts import DECLARACAO_CONCLUSAO_CURSO_PROMPT, PARECER_ASJUR_PAGS_FINAIS_PROMPT, PORTARIA_PROMPT, OFICIO_PROMPT, DECLARACAO_PROMPT, PARECER_CEPRO, DOE_PROMPT, PARECER_ASJUR_PAG_01_PROMPT, REPERCUSSAO_FINANCEIRA_TABLE_01_PROMPT, REPERCUSSAO_FINANCEIRA_TABLE_02_PROMPT, DIPLOMA_PROMPT

DOCUMENT_TYPES = {
    "PORTARIA": {"keywords": ["PORTARIA N", "RESOLVE", "PROMOVER", "TITULAÇÃO"], "prompt": PORTARIA_PROMPT},
    "OFICIO": {"keywords": ["OFÍCIO N", "SEDUC/SEC", "EXCELÊNCIA", "SECRETÁRIO"], "prompt": OFICIO_PROMPT},
    "DECLARACAO": {"keywords": ["DECLARAÇÃO", "DISPONIBILIDADE", "ORÇAMENTÁRIA", "FINANCEIRA", "UNIDADE", "PROJETO/ATIVIDADE"], "prompt": DECLARACAO_PROMPT},
    "PARECER_CEPRO": {"keywords": ["SEDUC/CEPRO", "SEDUC-CE", "RECONHECIMENTO", "CONSISTÊNCIA", "CONCLUÍDA"], "prompt": PARECER_CEPRO},
    "DOE": {"keywords": ["DIÁRIO", "OFICIAL", "ESTADO", "GOVERNADOR", "DECLARAR"], "prompt": DOE_PROMPT},
    "PARECER_ASJUR": {"keywords": ["SEDUC/ASJUR", "SEDUC/SEC", "COGEP/SEDUC", "CODIP", "JURÍDICA", "MINUTA"], "prompts": [PARECER_ASJUR_PAG_01_PROMPT, PARECER_ASJUR_PAGS_FINAIS_PROMPT]},
    "REPERCUSSAO_FINANCEIRA": {"keywords": ["REPERCUSSÃO", "FINANCEIRA", "ANUAL", "PATRONAL"], "prompts": [REPERCUSSAO_FINANCEIRA_TABLE_01_PROMPT, REPERCUSSAO_FINANCEIRA_TABLE_02_PROMPT]},
    "DIPLOMA": {"keywords": ["DIPLOMA", "CERTIFICADO"], "prompt": DIPLOMA_PROMPT,}
}

def detectar_tipo_documento(texto_pdf: str | None, content_type: str | None = None) -> str | None:
    if content_type == "DECLARACAO_CONCLUSAO_CURSO" or content_type == "declaracao_conclusao_curso":
        print("DEBUG: Documento identificado pelo content_type como 'DECLARACAO_CONCLUSAO_CURSO'")
        return "DECLARACAO_CONCLUSAO_CURSO"
    
    if content_type == "DOE":
        return "DOE"
    
    if content_type == "PARECER_CEPRO":
        return "PARECER_CEPRO"
    
    if content_type == "DIPLOMA":
        return "DIPLOMA"

    if not texto_pdf:
        return None

    for tipo, info in DOCUMENT_TYPES.items():
        keywords = info.get("keywords", [])
        if not keywords:
            continue

        presentes = [kw for kw in keywords if kw.lower() in texto_pdf.lower()]
        faltando = [kw for kw in keywords if kw.lower() not in texto_pdf.lower()]

        print(f"DEBUG: Keywords presentes: {presentes}")
        print(f"DEBUG: Keywords faltando: {faltando}")

        if presentes and not faltando:
            print(f"DEBUG: Documento identificado pelo texto como '{tipo}'")
            return tipo

    print("DEBUG: Nenhum tipo de documento identificado.")
    return None
