from .celery_app import app
from sqlalchemy.orm import Session
from ...database.session import get_db
from ...models.pdf import PDF
from typing import Optional
from ..text_structure import process_arquivo

@app.task(queue="estruturacao")
def combinar_paginas(results, file_id: int, doc_type: str):
    db: Session = next(get_db())
    try:
        db_pdf = db.query(PDF).filter(PDF.id == file_id).first()
        if not db_pdf:
            return f"PDF com ID {file_id} não encontrado."
        
    except Exception as e:
        pass
    finally:
        db.close()

@app.task(queue="estruturacao")
def estruturar_texto(file_id: int, prompt: str, doc_type: str, nome_servidor: Optional[str] = None) -> str:
    process_arquivo(file_id, prompt, doc_type, nome_servidor)
    return f"Texto estruturado com sucesso para PDF ID {file_id}."