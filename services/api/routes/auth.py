from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.api.auth import authenticate_user, create_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    user_id: str
    password: str
    role: str = "student"


class LoginRequest(BaseModel):
    user_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest) -> TokenResponse:
    if req.role not in ("student", "instructor", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    try:
        user = register_user(req.user_id, req.password, req.role)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    token = create_token(user["user_id"], user["role"])
    return TokenResponse(access_token=token, role=user["role"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest) -> TokenResponse:
    user = authenticate_user(req.user_id, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["user_id"], user["role"])
    return TokenResponse(access_token=token, role=user["role"])
