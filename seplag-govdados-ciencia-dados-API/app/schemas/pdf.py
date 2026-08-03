from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class PDFBase(BaseModel):
    fileNUP: str = Field(..., description="Número Único de Protocolo (NUP) do documento")
    filename: str = Field(..., description="Nome original do arquivo")
    process_date: date = Field(..., description="Data de abertura do processo do PDF no formato YYYY-MM-DD")
    content_type: str = Field(..., description="Tipo do arquivo")
    extracted_text: Optional[str] = Field(None, description="Texto extraído do PDF")
    status: Optional[str] = Field('Pendente',pattern=r'^(Pendente|Processando|Processado)$', description="Status do processamento do PDF")

class PDFCreate(PDFBase):
    file_byte: bytes = Field(..., description="Conteúdo binário do arquivo")
    

class PDFOut(PDFBase):
    uploaded_date: date = Field(..., description="Data de upload do PDF no formato YYYY-MM-DD")
    id: int
    owner_id: int
    
    class Config:
        orm_mode = True
