from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..models import (
    User as UserModel,
    UserRoleEnum
)
from typing import List, Optional
from uuid import UUID
from app.utils.logging_config import get_logger
from app.audit.utils import log_audit_entry

async def get_user(db: AsyncSession, user_id: UUID) -> Optional[UserModel]:
    """Get a user by ID"""
    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.tamanKehati))
        .filter(UserModel.id == user_id)
    )
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
    """Get a user by email"""
    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.tamanKehati))
        .filter(UserModel.email == email)
    )
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100, role: Optional[UserRoleEnum] = None, taman_kehati_id: Optional[int] = None):
    """Get a list of users with optional filtering"""
    query = select(UserModel).options(selectinload(UserModel.tamanKehati))
    
    if role is not None:
        query = query.filter(UserModel.role == role)
    
    if taman_kehati_id is not None:
        query = query.filter(UserModel.taman_kehati_id == taman_kehati_id)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def create_user(
    db: AsyncSession, 
    email: str, 
    password: str, 
    nama: str, 
    role: str = "viewer", 
    is_active: bool = True,
    taman_kehati_id: Optional[int] = None,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> UserModel:
    """Create a new user"""
    # Convert string role to enum if needed
    try:
        if isinstance(role, str):
            role_enum = UserRoleEnum(role)
        else:
            role_enum = role
    except ValueError:
        # Default to viewer if invalid role
        role_enum = UserRoleEnum.viewer
    
    db_user = UserModel(
        email=email,
        password=password,
        nama=nama,
        role=role_enum,
        is_active=is_active,
        taman_kehati_id=taman_kehati_id
    )
    db.add(db_user)
    await db.flush()  # Use flush to get the ID before committing
    
    # Log audit entry
    await log_audit_entry(
        db, 
        user_id=current_user_id, 
        action="CREATE", 
        table_name="users", 
        record_id=db_user.id,
        new_data={
            "id": str(db_user.id),
            "email": db_user.email,
            "nama": db_user.nama,
            "role": db_user.role.value if hasattr(db_user.role, 'value') else str(db_user.role),
            "is_active": db_user.is_active,
            "taman_kehati_id": db_user.taman_kehati_id
        },
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(
    db: AsyncSession,
    user_id: UUID,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    **kwargs
) -> Optional[UserModel]:
    """Update a user"""
    result = await db.execute(
        select(UserModel).filter(UserModel.id == user_id)
    )
    user = result.scalars().first()
    
    if not user:
        return None
    
    # Capture old data for audit
    old_data = {
        "id": str(user.id),
        "email": user.email,
        "nama": user.nama,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "is_active": user.is_active,
        "taman_kehati_id": user.taman_kehati_id
    }
    
    for field, value in kwargs.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    # Capture new data for audit
    new_data = {
        "id": str(user.id),
        "email": user.email,
        "nama": user.nama,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "is_active": user.is_active,
        "taman_kehati_id": user.taman_kehati_id
    }
    
    await db.commit()
    await db.refresh(user)
    
    # Log audit entry
    await log_audit_entry(
        db, 
        user_id=current_user_id, 
        action="UPDATE", 
        table_name="users", 
        record_id=user.id,
        old_data=old_data,
        new_data=new_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return user

async def delete_user(
    db: AsyncSession, 
    user_id: UUID, 
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """Delete a user"""
    result = await db.execute(
        select(UserModel).filter(UserModel.id == user_id)
    )
    user = result.scalars().first()
    
    if not user:
        return False
    
    # Capture old data for audit
    old_data = {
        "id": str(user.id),
        "email": user.email,
        "nama": user.nama,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "is_active": user.is_active,
        "taman_kehati_id": user.taman_kehati_id
    }
    
    await db.delete(user)
    await db.flush()  # Use flush to delete the user before logging
    
    # Log audit entry
    await log_audit_entry(
        db, 
        user_id=current_user_id, 
        action="DELETE", 
        table_name="users", 
        record_id=user.id,
        old_data=old_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    await db.commit()
    return True