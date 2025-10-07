from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.schemas.users import UserCreate, UserUpdate, UserResponse
from app.models import UserRoleEnum
from app.auth.utils import get_current_active_user, get_current_super_admin, get_current_admin
from app.crud.users import (
    get_user, 
    get_users, 
    create_user as create_user_db,
    update_user,
    delete_user
)
from app.utils.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0, 
    limit: int = 100,
    role: Optional[UserRoleEnum] = None,
    taman_kehati_id: Optional[int] = None,
    current_user = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get list of users with filtering (super_admin only)"""
    logger.info(f"Fetching users - user: {current_user.email}, skip: {skip}, limit: {limit}, role: {role}, taman_kehati_id: {taman_kehati_id}")
    users = await get_users(db, skip=skip, limit=limit, role=role, taman_kehati_id=taman_kehati_id)
    logger.info(f"Returned {len(users)} users")
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: str, 
    current_user = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user by ID (super admin only)"""
    logger.info(f"Fetching user {user_id} - requested by {current_user.email}")
    user = await get_user(db, user_id)
    if not user:
        logger.warning(f"User {user_id} not found - requested by {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    logger.info(f"Successfully fetched user {user_id}")
    return UserResponse.from_orm(user)

@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    current_user = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (super_admin only)"""
    logger.info(f"Creating new user {user.email} - requested by {current_user.email}")
    
    # Check if user already exists
    from app.auth.utils import get_user_by_email
    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        logger.warning(f"User creation failed - email already exists: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    from app.auth.utils import get_password_hash
    hashed_password = get_password_hash(user.password)
    
    # Create the user
    db_user = await create_user_db(
        db, 
        email=user.email, 
        password=hashed_password, 
        nama=user.nama,
        role=user.role,
        taman_kehati_id=user.taman_kehati_id,
        current_user_id=current_user.id
    )
    
    logger.info(f"Successfully created user {user.email}")
    return UserResponse.from_orm(db_user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: str,
    user_update: UserUpdate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a user (self non-role fields; super_admin may update role/status)"""
    logger.info(f"Updating user {user_id} - requested by {current_user.email}")
    
    # Check permissions
    from uuid import UUID
    user_uuid = UUID(user_id)
    
    if current_user.id == user_uuid:
        # User can update their own profile (except role and status)
        if user_update.role is not None or user_update.is_active is not None:
            # Only super_admin can change role or status
            if current_user.role != UserRoleEnum.super_admin:
                logger.warning(f"Unauthorized attempt to change role/status by user {current_user.email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only super_admin can update user role or status"
                )
    elif current_user.role == UserRoleEnum.super_admin:
        # Super admin can update any user
        pass
    else:
        # Regular users can't update other users
        logger.warning(f"Unauthorized attempt to update user {user_id} by user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Update the user
    update_data = user_update.dict(exclude_unset=True)
    # Don't allow password updates through this endpoint
    if 'password' in update_data:
        del update_data['password']
        
    db_user = await update_user(
        db, 
        user_id, 
        current_user_id=current_user.id,
        **update_data
    )
    if not db_user:
        logger.warning(f"User {user_id} not found for update")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"Successfully updated user {user_id}")
    return UserResponse.from_orm(db_user)

@router.delete("/{user_id}")
async def delete_user_endpoint(
    user_id: str,
    current_user = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user (super_admin only)"""
    logger.info(f"Deleting user {user_id} - requested by {current_user.email}")
    
    success = await delete_user(db, user_id, current_user_id=current_user.id)
    if not success:
        logger.warning(f"User {user_id} not found for deletion")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"Successfully deleted user {user_id}")
    return {"message": "User deleted successfully"}