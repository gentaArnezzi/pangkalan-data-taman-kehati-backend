"""
Dependency injection module for FastAPI
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from .database import get_db
from .auth.utils import (
    get_current_user,
    get_current_active_user,
    get_current_admin,
    get_current_super_admin
)

# Database dependency
get_db_session = get_db

# Auth dependencies
CurrentUser = Depends(get_current_user)
CurrentActiveUser = Depends(get_current_active_user)
CurrentAdmin = Depends(get_current_admin)
CurrentSuperAdmin = Depends(get_current_super_admin)