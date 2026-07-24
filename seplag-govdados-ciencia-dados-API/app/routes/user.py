from fastapi import APIRouter, Depends, HTTPException, status


from sqlalchemy.orm import Session

from typing import List

from ..database.session import get_db
from ..models.user import User
from ..utils.auth import get_current_user, create_access_token
from ..utils.security import get_password_hash, verify_password
from ..schemas.user import UserCreate, UserOut, Token, UserLogin


router = APIRouter()

@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="email já cadastrado")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        grade = user.grade,
        email = user.email,
        matric= user.matric,
        hashed_password=hashed_password,
        actual_grade=user.actual_grade,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()  
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha ou email inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    
    access_token = create_access_token(data={"sub": db_user.email})  
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user
