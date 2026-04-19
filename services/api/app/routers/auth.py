from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from cdp_shared.db import get_db
from cdp_shared.models.admin_user import AdminUser
from app.auth.jwt import verify_password, create_access_token, hash_password

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(AdminUser).where(AdminUser.email == body.email)).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.email, user.role)
    return TokenResponse(access_token=token)


class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: str = "analyst"


@router.post("/users", status_code=201)
def create_user(body: CreateUserRequest, db: Session = Depends(get_db)):
    existing = db.execute(select(AdminUser).where(AdminUser.email == body.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = AdminUser(email=body.email, password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.commit()
    return {"id": str(user.id), "email": user.email, "role": user.role}
