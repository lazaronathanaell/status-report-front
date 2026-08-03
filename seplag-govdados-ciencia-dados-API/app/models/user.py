from sqlalchemy import Column, Integer, String, Boolean, PickleType
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship
from ..database.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    grade = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    matric = Column(MutableList.as_mutable(PickleType), nullable=True)
    actual_grade = Column(String, nullable=True)
    
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    pdfs = relationship("PDF", back_populates="owner")