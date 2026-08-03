from sqlalchemy import Column, Integer, String,LargeBinary, ForeignKey, Date,JSON

from sqlalchemy.orm import relationship
from ..database.base_class import Base

class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(Integer, primary_key=True, index=True)
    fileNUP = Column(String, unique=False, index=True, nullable=False)
    filename = Column(String, index=False, nullable=False)
    content_type = Column(String, nullable=False)
    file_byte = Column(LargeBinary, nullable=False)
    extracted_text = Column(String, nullable=True)
    process_date = Column(Date, nullable=False)
    uploaded_date = Column(Date, nullable=False)
    structured_text = Column(JSON, nullable=True)   
    status = Column(String, default='Pendente', nullable=False)  
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="pdfs")