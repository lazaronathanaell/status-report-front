# Task principal de extração
from .celery_app import app


from sqlalchemy.orm import Session
from ...database.session import get_db
from ...models.pdf import PDF
from ...models.user import User

from ..report_generation import (
    generate_docs_list,
    fill_template_report_positive,
    fill_template_report_negative,
)

from pathlib import Path

def get_template_path(filename: str) -> Path:
    # __file__ é o caminho do script text_extract.py
    base_dir = Path(__file__).resolve().parent.parent.parent.parent  # sobe até /projeto
    return base_dir / "templates" / filename


@app.task(bind=True, queue="relatorios", max_retries=5, default_retry_delay=60)
def generate_report_user(self, user_id: int):
    db: Session = next(get_db())
    try:
        # 1️⃣ Buscar usuário
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return f"Usuário com ID {user_id} não encontrado."

        # 2️⃣ Buscar todos os PDFs estruturados e validados do usuário
        pdfs = (
            db.query(PDF)
            .filter(PDF.owner_id == user.id, PDF.structured_text.isnot(None))
            .all()
        )
        if not pdfs:
            return f"Nenhum PDF estruturado encontrado para o usuário {user_id}."

        # 3️⃣ Montar o dicionário jsons_concatenados (substitui ler_jsons_concatenados)
        jsons_concatenados = {}
        for pdf in pdfs:
            try:
                conteudo = pdf.structured_text  # já é JSON no banco
                doc_type = pdf.content_type.upper().replace(" ", "_")
                jsons_concatenados[doc_type] = conteudo
            except Exception as e:
                print(f"Erro ao processar PDF {pdf.id}: {e}")

        # 4️⃣ Lógica de validação (mesma da função original)
        validation_failed = False
        failing_context = ""

        for chave_json, dados_doc in jsons_concatenados.items():
            validado = dados_doc.get("documento_validado", {})
            if validado and validado.get("documento_validado") is False:
                validation_failed = True
                failing_context += f"\n- Documento {chave_json}: {validado.get('contexto', 'Sem contexto informado')}"

        # 5️⃣ Geração do relatório (usando tuas funções originais)
        if validation_failed:
            report = fill_template_report_negative(jsons_concatenados, failing_context, get_template_path("report_template_negative.md"))
        else:
            docs_list = generate_docs_list(jsons_concatenados)
            report = fill_template_report_positive(jsons_concatenados, docs_list, get_template_path("report_template.md"))

        # 6️⃣ Salvar resultado
        # salvar no banco
        # enviar para topico do kafka

        print(report) 

        return f"Relatório gerado com sucesso para o usuário {user_id}."

    except self.MaxRetriesExceededError:
        return f"Relatório não pôde ser gerado após várias tentativas."
    except Exception as e:
        return f"Erro ao gerar relatório para usuário {user_id}: {str(e)}"
    finally:
        db.close()