# import os
# import logging
# from typing import Optional
# from celery import Celery, chord, chain
# import fitz
# from fitz import Document
# from io import BytesIO
# from sqlalchemy.orm import Session
# from sqlalchemy import func
# import re



# from ..database.session import get_db
# from ..models.pdf import PDF
# from ..models.user import User
# from .text_structure import process_arquivo
# from .extraction.table_extraction import extrair_tabelas_pymupdf, processar_pdf_tabelas_pg_01, processar_pdf_tabelas_pg_02
# from .extraction.text_extractor import check_hybrid_pdf_and_extract
# from .extraction.context_extractor import extrair_contexto_reduzido, extrair_nome_servidor

# from .validation.docs.portaria_validator import validation_portaria
# from .validation.docs.doe_validator import validation_doe
# from .validation.docs.oficio_validator import validation_oficio
# from .validation.docs.parecer_cepro_validator import validation_parecer_cepro
# from .validation.docs.parecer_asjur_validator import validation_parecer_asjur
# from .validation.docs.declaracao_conclusao_validator import validation_declaracao_conclusao
# from .validation.docs.declaracao_orcamentaria_validator import validation_declaracao
# from .validation.docs.repercussao_validator import validation_repercussao
# from .validation.docs.diploma_validator import validation_diploma


# from .constants.doc_types import DocTypes, DOCUMENT_TYPES

# from .report_generation import (
#     generate_docs_list,
#     fill_template_report_positive,
#     fill_template_report_negative,
# )



# REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# app = Celery(
#     'Extract_text',
#     broker=REDIS_URL,
#     backend=REDIS_URL
# )





# # def extract_text(file_bytes: bytes) -> str:
# #     doc = Document(stream=BytesIO(file_bytes), filetype="pdf")
# #     text = "".join([f'{page.get_text()}\f' for page in doc])
# #     return text









