import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from utils.auth import hash_password, verify_password, create_access_token, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterUserRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new educator account."""
    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    # Check if user email exists
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    hashed_pw = hash_password(body.password)
    new_user = User(
        email=body.email.lower(),
        hashed_password=hashed_pw,
        full_name=body.full_name,
        tier="free"
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_access_token({"sub": new_user.id, "email": new_user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user.to_dict()
    }

@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(
    body: LoginUserRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate with email and password to receive a JWT access token."""
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated."
        )

    token = create_access_token({"sub": user.id, "email": user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve current authenticated user profile with automatic 30-day quota cycle renewal."""
    from utils.usage_limits import refresh_user_quota_if_due
    if refresh_user_quota_if_due(current_user):
        await db.commit()
        await db.refresh(current_user)
    return {"user": current_user.to_dict()}
