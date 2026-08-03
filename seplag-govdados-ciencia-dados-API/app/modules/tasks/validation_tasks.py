# Task principal de extração
from .celery_app import app


from ..constants.doc_types import DocTypes, DOCUMENT_TYPES
from sqlalchemy.orm import Session
from sqlalchemy import func
from ...database.session import get_db
from ...models.pdf import PDF
from ...models.user import User

from ..validation.docs.portaria_validator import validation_portaria
from ..validation.docs.doe_validator import validation_doe
from ..validation.docs.oficio_validator import validation_oficio
from ..validation.docs.parecer_cepro_validator import validation_parecer_cepro
from ..validation.docs.parecer_asjur_validator import validation_parecer_asjur
from ..validation.docs.declaracao_conclusao_validator import validation_declaracao_conclusao
from ..validation.docs.declaracao_orcamentaria_validator import validation_declaracao
from ..validation.docs.repercussao_validator import validation_repercussao
from ..validation.docs.diploma_validator import validation_diploma

@app.task(bind=True, queue="validacao", max_retries=10, default_retry_delay=60)
def validacao_doc(self, file_id: int, doc_type: str) -> str:
    db: Session = next(get_db())
    try:
        if doc_type == DocTypes.PORTARIA.value or doc_type == DocTypes.PORTARIA.value.lower():
            portaria = db.query(PDF).filter(PDF.id == file_id).first()
            if not portaria:
                return f"Documento com ID {file_id} não encontrada."

            user = db.query(User).filter(User.id == portaria.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."

            doe = (
                db.query(PDF)
                .filter(PDF.owner_id == user.id, 
                       func.lower(PDF.content_type) == func.lower(DocTypes.DOE.value))
                .first()
            )
            if not doe:
                raise self.retry(exc=Exception("DOE estruturado não encontrado ainda."))

            validation_portaria(file_id, portaria, doe, user)

        elif doc_type == DocTypes.OFICIO.value or doc_type == DocTypes.OFICIO.value.lower():
            oficio = db.query(PDF).filter(PDF.id == file_id).first()
            if not oficio:
                return f"Documento com ID {file_id} não encontrado."

            user = db.query(User).filter(User.id == oficio.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."

            portaria = (
                db.query(PDF)
                .filter(PDF.owner_id == user.id, PDF.content_type == DocTypes.PORTARIA.value, PDF.structured_text.isnot(None))
                .first()
            )
            if not portaria:
                raise self.retry(exc=Exception("Portaria estruturada não encontrada ainda."))

            validation_oficio(file_id, oficio, portaria, user)


        elif doc_type == DocTypes.DOE.value or doc_type == DocTypes.DOE.value.lower():
            doe = db.query(PDF).filter(PDF.id == file_id).first()
            if not doe:
                return f"Documento com ID {file_id} não encontrado."

            user = db.query(User).filter(User.id == doe.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."

            validation_doe(file_id, doe, user)

        elif doc_type == DocTypes.PARECER_CEPRO.value or doc_type == DocTypes.PARECER_CEPRO.value.lower():
            parecer_cepro = db.query(PDF).filter(PDF.id == file_id).first()
            if not parecer_cepro:
                return f"Documento com ID {file_id} não encontrado."

            user = db.query(User).filter(User.id == parecer_cepro.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."
            
            diploma_em_confeccao = parecer_cepro.structured_text.get("diploma_em_confeccao", False)

            declaracao_conclusao = None

            if diploma_em_confeccao:
            
                declaracao_conclusao = (
                    db.query(PDF)
                    .filter(PDF.owner_id == user.id, PDF.content_type == DocTypes.DECLARACAO_CONCLUSAO_CURSO.value, PDF.structured_text.isnot(None))
                    .first()
                )

                if not declaracao_conclusao:
                     raise self.retry(exc=Exception("DECLARAÇÃO DE CONCLUSÃO CURSO estruturado não encontrado ainda."))

            validation_parecer_cepro(file_id, parecer_cepro, declaracao_conclusao, user)

        elif doc_type == DocTypes.PARECER_ASJUR.value or doc_type == DocTypes.PARECER_ASJUR.value.lower():
            parecer_asjur = db.query(PDF).filter(PDF.id == file_id).first()
            if not parecer_asjur:
                return f"Documento com ID {file_id} não encontrado."

            user = db.query(User).filter(User.id == parecer_asjur.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."

            validation_parecer_asjur(file_id, parecer_asjur, user)

        elif doc_type == DocTypes.DECLARACAO_CONCLUSAO_CURSO.value or doc_type == DocTypes.DECLARACAO_CONCLUSAO_CURSO.value.lower():
            declaracao_conclusao = db.query(PDF).filter(PDF.id == file_id).first()
            if not declaracao_conclusao:
                return f"Documento com ID {file_id} não encontrado."

            user = db.query(User).filter(User.id == declaracao_conclusao.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."

            validation_declaracao_conclusao(file_id, declaracao_conclusao, user)


        elif doc_type == DocTypes.DIPLOMA.value or doc_type == DocTypes.DIPLOMA.value.lower():
            diploma = db.query(PDF).filter(PDF.id == file_id).first()
            if not diploma:
                return f"Documento com ID {file_id} não encontrado."

            user = db.query(User).filter(User.id == diploma.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."

            validation_diploma(file_id, diploma, user)

        elif doc_type == DocTypes.DECLARACAO.value or doc_type == DocTypes.DECLARACAO.value.lower():
            declaracao = db.query(PDF).filter(PDF.id == file_id).first()
            if not declaracao:
                return f"Documento com ID {file_id} não encontrado."

            user = db.query(User).filter(User.id == declaracao.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."

            repercussao = (
                db.query(PDF)
                .filter(PDF.owner_id == user.id, PDF.content_type == DocTypes.REPERCUSSAO_FINANCEIRA.value, PDF.structured_text.isnot(None))
                .first()
            )
            if not repercussao:
                raise self.retry(exc=Exception("Repercussão Financeira estruturada não encontrada ainda."))

            validation_declaracao(file_id, declaracao, repercussao, user)

        elif doc_type == DocTypes.DECLARACAO_ANO_ANTERIOR.value or doc_type == DocTypes.DECLARACAO_ANO_ANTERIOR.value.lower():
            declaracao_ano_anterior = db.query(PDF).filter(PDF.id == file_id).first()
            if not declaracao_ano_anterior:
                return f"Documento com ID {file_id} não encontrado."

            user = db.query(User).filter(User.id == declaracao_ano_anterior.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."

            repercussao = (
                db.query(PDF)
                .filter(PDF.owner_id == user.id, PDF.content_type == DocTypes.REPERCUSSAO_FINANCEIRA.value, PDF.structured_text.isnot(None))
                .first()
            )
            if not repercussao:
                raise self.retry(exc=Exception("Repercussão Financeira estruturada não encontrada ainda."))

            validation_declaracao(file_id, declaracao_ano_anterior, repercussao, user)

        elif doc_type == DocTypes.REPERCUSSAO_FINANCEIRA.value or doc_type == DocTypes.REPERCUSSAO_FINANCEIRA.value.lower():
            repercussao = db.query(PDF).filter(PDF.id == file_id).first()
            if not repercussao:
                return f"Documento com ID {file_id} não encontrado."

            user = db.query(User).filter(User.id == repercussao.owner_id).first()
            if not user:
                return f"Usuário do documento {file_id} não encontrado."
            
            validation_repercussao(file_id, repercussao, user)

        return f"Texto validado com sucesso para PDF ID {file_id}."
    except self.MaxRetriesExceededError:
        return f"Validação não realizada: DOE estruturado não encontrado após várias tentativas."
    except Exception as e:
        return f"Erro na validação do PDF ID {file_id}: {str(e)}"
    finally:
        db.close()