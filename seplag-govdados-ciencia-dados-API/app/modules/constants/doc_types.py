from enum import Enum
from typing import Dict, List, Union, Optional
from dataclasses import dataclass

@dataclass
class DocumentType:
    keywords: List[str]
    prompt: Optional[str] = None
    prompts: Optional[List[str]] = None

class DocTypes(Enum):
    PORTARIA = "PORTARIA"
    OFICIO = "OFICIO" 
    DECLARACAO = "DECLARACAO"
    PARECER_CEPRO = "PARECER_CEPRO"
    DOE = "DOE"
    PARECER_ASJUR = "PARECER_ASJUR"
    REPERCUSSAO_FINANCEIRA = "REPERCUSSAO_FINANCEIRA"
    DECLARACAO_CONCLUSAO_CURSO = "DECLARACAO_CONCLUSAO_CURSO"
    DECLARACAO_ANO_ANTERIOR = "DECLARACAO_ANO_ANTERIOR"
    DIPLOMA = "DIPLOMA"

DOCUMENT_TYPES: Dict[str, DocumentType] = {
    DocTypes.PORTARIA.value: DocumentType(
        keywords=["PORTARIA N", "RESOLVE", "PROMOVER", "TITULAÇÃO"],
        prompt="PORTARIA_PROMPT"
    ),
    DocTypes.OFICIO.value: DocumentType(
        keywords=["OFÍCIO N", "SEDUC/SEC", "EXCELÊNCIA", "SECRETÁRIO"],
        prompt="OFICIO_PROMPT"
    ),
    DocTypes.DECLARACAO.value: DocumentType(
        keywords=["DECLARAÇÃO", "DISPONIBILIDADE", "ORÇAMENTÁRIA", "FINANCEIRA", "UNIDADE", "PROJETO/ATIVIDADE"],
        prompt="DECLARACAO_PROMPT"
    ),
    DocTypes.PARECER_CEPRO.value: DocumentType(
        keywords=["SEDUC/CEPRO", "SEDUC-CE", "RECONHECIMENTO", "CONSISTÊNCIA", "CONCLUÍDA"],
        prompt="PARECER_CEPRO"
    ),
    DocTypes.DOE.value: DocumentType(
        keywords=["DIÁRIO", "OFICIAL", "ESTADO", "GOVERNADOR", "DECLARAR"],
        prompt="DOE_PROMPT"
    ),
    DocTypes.PARECER_ASJUR.value: DocumentType(
        keywords=["SEDUC/ASJUR", "SEDUC/SEC", "COGEP/SEDUC", "CODIP", "JURÍDICA", "MINUTA"],
        prompts=["PARECER_ASJUR_PAG_01_PROMPT", "PARECER_ASJUR_PAGS_FINAIS_PROMPT"]
    ),
    DocTypes.REPERCUSSAO_FINANCEIRA.value: DocumentType(
        keywords=["REPERCUSSÃO", "FINANCEIRA", "ANUAL", "PATRONAL"],
        prompts=["REPERCUSSAO_FINANCEIRA_TABLE_01_PROMPT", "REPERCUSSAO_FINANCEIRA_TABLE_02_PROMPT"]
    )
}