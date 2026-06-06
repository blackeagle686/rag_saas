"""
Authentication endpoints for the RAGaaS platform.

Handles user registration and login (generating JWTs).
"""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.security import create_access_token, get_password_hash, verify_password
from db.engine import get_db_session
from db.models.tenant import Tenant, TenantPlan, TenantStatus

router = APIRouter(prefix="/v1/auth", tags=["Auth"])

# Schemas
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    # Check if user already exists
    result = await db.execute(select(Tenant).where(Tenant.email == request.email))
    existing_tenant = result.scalars().first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new tenant
    tenant = Tenant(
        id=uuid.uuid4(),
        name=request.name,
        email=request.email,
        password_hash=get_password_hash(request.password),
        plan=TenantPlan.STARTER,
        status=TenantStatus.ACTIVE,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    # Generate JWT
    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": str(tenant.id)}, expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    # Find user by email
    result = await db.execute(select(Tenant).where(Tenant.email == request.email))
    tenant = result.scalars().first()
    
    if not tenant or not verify_password(request.password, tenant.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Generate JWT
    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": str(tenant.id)}, expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token, token_type="bearer")
