from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List

class UserBase(BaseModel):
    grade: str = Field(..., pattern=r'^(Especialização|Mestrado|Doutorado)$')
    full_name: Optional[str] = None
    email: EmailStr
    matric: Optional[List[str]] = None
    actual_grade: Optional[str] = None
    

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserOut(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr  
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str