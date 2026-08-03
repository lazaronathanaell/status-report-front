# Task principal de extração
from .celery_app import app

import logging
from celery import chord, chain
from sqlalchemy.orm import Session
from ...database.session import get_db
from ...models.pdf import PDF
from ...models.user import User

from ..extraction.text_extractor import check_hybrid_pdf_and_extract
from ..extraction.document_detector import detectar_tipo_documento
from ..extraction.context_extractor import extrair_contexto_reduzido, extrair_nome_servidor, contexto_reduzido_diploma
from ..extraction.table_extraction import extrair_tabelas_pymupdf, processar_pdf_tabelas_pg_01, processar_pdf_tabelas_pg_02

from .structure_tasks import estruturar_texto, combinar_paginas
from .validation_tasks import validacao_doc


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

@app.task(bind=True, queue="extracao")
def extract_text_from_file(self, file_id: int, user_id: int):
    db: Session = next(get_db())
    try:
        db_pdf = db.query(PDF).filter(PDF.id == file_id, PDF.owner_id == user_id).first()
        if not db_pdf:
            return f"PDF com ID {file_id} não encontrado."
        
        user = db.query(User).filter(User.id ==  user_id).first()
        if not user:
            return f"User com ID {user_id} não encontrado."

        db_pdf.status = 'Processando'
        db.commit()

        file_bytes = db_pdf.file_byte

        content_type = db_pdf.content_type

        tipo_doc = None

        if content_type == "DIPLOMA" or content_type == "diploma":
            extracted_text, status = check_hybrid_pdf_and_extract(file_bytes, 1, True)
            logging.info(status)
            tipo_doc = "DIPLOMA"

            nome_servidor = str(user.full_name)

            tipo_documento = status[0].get("type", "")
            
            extracted_text = contexto_reduzido_diploma(extracted_text, nome_servidor, linhas_acima=4, linhas_abaixo=8)
            
        else:
            extracted_text, status = check_hybrid_pdf_and_extract(file_bytes)

            logging.info(status)

            content_type = db_pdf.content_type

            tipo_doc = detectar_tipo_documento(extracted_text, content_type)

            # Extrair contexto reduzido para o documento DIÁRIO OFICIAL DO ESTADO
            if tipo_doc == "DOE":
                nome_servidor = str(user.full_name)

                tipo_documento = status[0].get("type", "")
                
                extracted_text = extrair_contexto_reduzido(extracted_text, nome_servidor, tipo_documento)
            
        
        db_pdf.extracted_text = extracted_text
        db_pdf.status = 'Processado'
        db.commit()

        if tipo_doc:
            if tipo_doc == "DECLARACAO_CONCLUSAO_CURSO":
                chain(
                    estruturar_texto.si(
                        file_id, 
                        DECLARACAO_CONCLUSAO_CURSO_PROMPT, 
                        tipo_doc
                    ),
                    validacao_doc.si(file_id, tipo_doc)
                ).apply_async(queue="estruturacao")

            elif tipo_doc == "REPERCUSSAO_FINANCEIRA":
                tasks = []
                
                nome_original = str(user.full_name)
                nome_servidor = extrair_nome_servidor(extracted_text, nome_original)

                pag0 = processar_pdf_tabelas_pg_01(file_bytes, [1], extrair_tabelas_pymupdf)  
                prompt_pag0 = f"{DOCUMENT_TYPES[tipo_doc]['prompts'][0]}\n\n{pag0}"
                tasks.append(
                    estruturar_texto.s(
                        file_id=file_id,
                        prompt=prompt_pag0,
                        doc_type="REPERCUSSAO_FINANCEIRA_TABLE_01_PROMPT")
                )

                pag1 = processar_pdf_tabelas_pg_02(file_bytes, [2], extrair_tabelas_pymupdf)  
                prompt_pag1 = f"{DOCUMENT_TYPES[tipo_doc]['prompts'][1]}\n\n{pag1}"
                tasks.append(
                    estruturar_texto.s(
                        file_id=file_id,
                        prompt=prompt_pag1,
                        doc_type="REPERCUSSAO_FINANCEIRA_TABLE_02_PROMPT",
                        nome_servidor = nome_servidor
                        )
                )

                chord(tasks)(
                    combinar_paginas.s(file_id, tipo_doc) | validacao_doc.si(file_id, tipo_doc)
                )

            elif tipo_doc == "PARECER_ASJUR":
                paginas = extracted_text.split("\f")[:-1]  # Remove a última página em branco
                pag1 = paginas[0]
                pag_finais = paginas[-2:] if len(paginas) > 3 else paginas[1:]

                tasks = []

                prompt_pag1 = f"{DOCUMENT_TYPES[tipo_doc]['prompts'][0]}\n\n{pag1}"
                tasks.append(
                    estruturar_texto.s(file_id=file_id, prompt=prompt_pag1, doc_type="PARECER_ASJUR_01")
                )
                prompt_pag = DOCUMENT_TYPES[tipo_doc]['prompts'][1] + ''.join([f"\n\n{pag}" for pag in pag_finais])

                tasks.append(
                    estruturar_texto.s(file_id=file_id, prompt=prompt_pag, doc_type="PARECER_ASJUR_PAGS_FINAIS")
                )

                chord(tasks)((combinar_paginas.s(file_id, tipo_doc) | validacao_doc.si(file_id, tipo_doc))
            )

            else:
                prompt = DOCUMENT_TYPES[tipo_doc]["prompt"]

                chain(
                    estruturar_texto.si(file_id, prompt, tipo_doc),
                    validacao_doc.si(file_id, tipo_doc)
                ).apply_async()
               
            return f"Texto extraído e documento identificado como '{tipo_doc}' para o PDF ID {file_id}."
        else:
            return f"Tipo de documento não identificado para o PDF ID {file_id}. Estruturação não iniciada."

    except Exception as e:
        if 'db_pdf' in locals() and db_pdf:
            db_pdf.status = 'Pendente'
            db.commit()
        return f"Erro na extração do PDF ID {file_id}: {str(e)}"

    finally:
        db.close()