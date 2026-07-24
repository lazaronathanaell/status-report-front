from app.modules.tasks.report_tasks import generate_report_user
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from datetime import datetime
from io import BytesIO
from sqlalchemy.orm import Session
from typing import List
import os
import io
import fitz
from  celery import Celery

from ..database.session import get_db
from ..modules.tasks.extraction_tasks import extract_text_from_file 
from ..modules.tasks.celery_app import app as celery_app
from ..models.pdf import PDF
from ..models.user import User
from ..utils.auth import get_current_user
from ..schemas.pdf import PDFCreate, PDFOut

router = APIRouter()

@router.post("/", response_model=PDFOut)
async def upload_pdf(
    title: str,
    fileNUP: str,
    content_type: str,
    process_date: datetime,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.content_type =='application/pdf':
        raise HTTPException(status_code=400, detail="Apenas arquivos PDFs são permitidos")
    
    try:
            contents = await file.read()
            pdf_stream = io.BytesIO(contents)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            
            pages_text = []
            
            for page_num, page in enumerate(doc, start=1):
                pages_text.append({
                    "page_number": page_num,
                    "text": page.get_text()
                })
            extracted_text = "\n".join([page["text"] for page in pages_text])
    except Exception as e:
        raise HTTPException(500, detail=f"Error processing PDF: {str(e)}")
    finally:
        await file.close()

    db_pdf = PDF(
        filename=title,
        fileNUP=fileNUP,
        content_type=None,
        file_byte=contents,
        extracted_text=extracted_text,
        process_date = process_date,
        uploaded_date=datetime.now().date(),
        owner_id=current_user.id
    )
    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)
    return {
        "id": db_pdf.id,
        "filename": db_pdf.filename,
        "fileNUP": db_pdf.fileNUP,
        "content_type": db_pdf.content_type,
        "uploaded_date": db_pdf.uploaded_date,
        "owner_id": db_pdf.owner_id
    }

@router.get("/", response_model=List[PDFOut])
def list_pdfs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pdfs = db.query(PDF).filter(PDF.owner_id == current_user.id).offset(skip).limit(limit).all()
    return pdfs


@router.get("/{pdf_id}/content")
def get_pdf_content(
    pdf_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
  
    pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.owner_id == current_user.id).first()
    

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF não encontrado")
    


    file_like = BytesIO(pdf.file_byte)
    file_like.seek(0)  
    

    return StreamingResponse(
        file_like, 
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=arquivo.pdf"}
    )




@router.get("/by-nup/{nup}", response_model=PDFOut)
def get_pdf_by_nup(
    nup: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Buscar o PDF pelo NUP e garantir que pertence ao usuário atual
    pdf = db.query(PDF).filter(PDF.fileNUP == nup, PDF.owner_id == current_user.id).first()
    
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF não encontrado")
    
    return pdf



@router.post("/portaria")
async def portaria_pdf(
    title: str | None,
    fileNUP: str | None,
    content_type: str | None,
    process_date: datetime,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) 
) -> dict:
    headers = {"Content-Type": "application/json"}

    documento_validado = {
        "documento_validado": True,
        "contexto": "Documento Válido."
    }

    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Apenas arquivos PDFs são permitidos")

    file_bytes = await file.read()

    db_pdf = PDF(
        filename=title,
        fileNUP=fileNUP,
        process_date=process_date,
        content_type=content_type,
        file_byte=file_bytes,
        uploaded_date=datetime.now().date(),
        owner_id=current_user.id,
        status='Pendente'
    )

    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)

    extract_map = {
        'file_id': db_pdf.id,
        'user_id': current_user.id
    }
    
    extract_text_from_file.apply_async(kwargs=extract_map)

    generate_report_user.apply_async(kwargs={'user_id': current_user.id})

    return JSONResponse(
        {
            "status": "DOCUMENTO RECEBIDO E ENVIADO PARA PROCESSAMENTO",
            "documento_validado": documento_validado
        },
        status_code=200,
        headers=headers,
    )

@router.get("/{pdf_id}/extraction-status")
def extraction_status(
    pdf_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.owner_id == current_user.id).first()

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF não encontrado")

    return {
        "id": pdf.id,
        "status": pdf.status,
        "extracted_text": pdf.extracted_text if pdf.status == "Processado" else None
    }

@router.get("/{pdf_id}/structure-status")
def structure_status(
    pdf_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.owner_id == current_user.id).first()

    if not pdf:
        raise HTTPException(status_code=404, detail="PDF não encontrado")

    return {
        "id": pdf.id,
        "structured_text": pdf.structured_text if pdf.status == "Processado" else None
    }

@router.get("/structured-all")
def structured_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Busca PDFs do usuário com status "Processado"
    pdfs = (
        db.query(PDF)
        .filter(PDF.owner_id == current_user.id, PDF.status == "Processado")
        .order_by(PDF.id.desc())
        .all()
    )

    # Se não houver PDFs processados
    if not pdfs:
        return {
            "count": 0,
            "results": []
        }

    # Monta o retorno
    results = []
    for pdf in pdfs:
        results.append({
            "id": pdf.id,
            "filename": pdf.filename,
            "fileNUP": pdf.fileNUP,
            "process_date": pdf.process_date,
            "structured_text": pdf.structured_text
        })

    return {
        "count": len(results),
        "results": results
    }



@router.delete("/{pdf_id}")
def delete_pdf(
    pdf_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.owner_id == current_user.id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF não encontrado")
    
    db.delete(pdf)
    db.commit()
    return {"message": "PDF Removido com sucesso"}