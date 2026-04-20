from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from cdp_shared.db import get_db
from cdp_shared.models.admin_user import AdminUser
from app.auth.jwt import verify_password, create_access_token, hash_password, require_role

router = APIRouter()
_optional_bearer = HTTPBearer(auto_error=False)


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
def create_user(
    body: CreateUserRequest,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer),
):
    user_count = db.execute(select(func.count()).select_from(AdminUser)).scalar()

    if user_count == 0:
        # Bootstrap: allow first admin without auth
        body.role = "admin"
    else:
        # After bootstrap: require an authenticated admin
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        # Reuse require_role dependency inline
        from app.auth.jwt import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials as Creds
        from jose import JWTError, jwt
        from cdp_shared.config import settings
        try:
            payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            caller_email = payload.get("sub")
            caller_role = payload.get("role")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        if caller_role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create users")

    existing = db.execute(select(AdminUser).where(AdminUser.email == body.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = AdminUser(email=body.email, password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.commit()
    return {"id": str(user.id), "email": user.email, "role": user.role}


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: AdminUser = Depends(require_role("admin"))):
    users = db.execute(select(AdminUser)).scalars().all()
    return [{"id": str(u.id), "email": u.email, "role": u.role, "created_at": u.created_at} for u in users]
