from datetime import datetime, timedelta, timezone
from typing import Any, Union, List, Optional
import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token",
    auto_error=False
)

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

class UserRole:
    ADMIN = "ADMIN"
    PLANT_MANAGER = "PLANT_MANAGER"
    MAINTENANCE_MANAGER = "MAINTENANCE_MANAGER"
    ENGINEER = "ENGINEER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"
    
    ALL_ROLES = [ADMIN, PLANT_MANAGER, MAINTENANCE_MANAGER, ENGINEER, OPERATOR, VIEWER]
    WRITE_ROLES = [ADMIN, PLANT_MANAGER, MAINTENANCE_MANAGER, ENGINEER, OPERATOR]
    MAINTENANCE_ROLES = [ADMIN, PLANT_MANAGER, MAINTENANCE_MANAGER, ENGINEER]
    ENGINEERING_ROLES = [ADMIN, ENGINEER]
    ADMIN_ROLES = [ADMIN, PLANT_MANAGER]

def create_access_token(
    subject: Union[str, Any], role: str = UserRole.VIEWER, expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "role": role}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(
            sub=payload.get("sub"),
            role=payload.get("role"),
            exp=payload.get("exp")
        )
        return token_data
    except JWTError:
        return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8")[:72], salt).decode("utf-8")

async def get_current_user_payload(token: Optional[str] = Depends(oauth2_scheme)) -> TokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    payload = verify_token(token)
    if payload is None or payload.sub is None:
        raise credentials_exception
    return payload

async def get_optional_user_payload(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[TokenPayload]:
    if not token:
        return None
    return verify_token(token)

def require_roles(allowed_roles: List[str]):
    async def role_checker(token_payload: TokenPayload = Depends(get_current_user_payload)):
        if token_payload.role not in allowed_roles and token_payload.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return token_payload
    return role_checker

