from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.settings import settings
from app.auth.utils import authenticate_user, get_password_hash, get_current_active_user
from app.core.security import create_access_token
from app.models import User as UserModel, UserRoleEnum
from app.schemas.users import UserCreate, UserResponse, Token, TokenData
from app.crud.users import get_user_by_email, create_user as create_user_db
from app.utils.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/auth/register", response_model=UserResponse,
             summary="Register new user",
             description="Register a new user (super_admin only)",
             responses={
                 200: {
                     "description": "User successfully registered",
                     "content": {
                         "application/json": {
                             "example": {
                                 "id": "123e4567-e89b-12d3-a456-426614174000",
                                 "email": "newuser@example.com",
                                 "nama": "New User",
                                 "role": "viewer",
                                 "is_active": True,
                                 "taman_kehati_id": 1,
                                 "created_at": "2023-01-01T00:00:00",
                                 "updated_at": "2023-01-01T00:00:00"
                             }
                         }
                     }
                 }
             })
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    """Register a new user (super_admin only)"""
    # Only super_admins can register users
    if current_user.role != UserRoleEnum.super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin users can register new users"
        )
    
    logger.info(f"Registration attempt for email: {user_data.email} by user {current_user.email}")
    
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        logger.warning(f"Registration failed - email already exists: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create the user
    user = await create_user_db(
        db, 
        email=user_data.email, 
        password=hashed_password, 
        nama=user_data.nama,
        role=user_data.role,
        taman_kehati_id=user_data.taman_kehati_id,
        current_user_id=current_user.id if current_user else None
    )
    
    logger.info(f"Successfully registered user: {user_data.email}")
    return UserResponse.from_orm(user)

@router.post("/auth/login", response_model=Token, 
             summary="User login",
             description="Authenticate user and return access and refresh tokens",
             responses={
                 200: {
                     "description": "Successful login",
                     "content": {
                         "application/json": {
                             "example": {
                                 "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                 "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                 "token_type": "bearer",
                                 "user": {
                                     "id": "123e4567-e89b-12d3-a456-426614174000",
                                     "email": "admin@example.com",
                                     "nama": "Admin User",
                                     "role": "super_admin",
                                     "is_active": True,
                                     "taman_kehati_id": 1,
                                     "created_at": "2023-01-01T00:00:00",
                                     "updated_at": "2023-01-01T00:00:00"
                                 }
                             }
                         }
                     }
                 }
             })
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login endpoint that returns access and refresh tokens"""
    logger.info(f"Login attempt for email: {form_data.username}")
    
    try:
        user = await authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning(f"Login failed - invalid credentials for email: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get the full user object from DB for role checking
        db_user = await get_user_by_email(db, user.email)
        if not db_user or not db_user.is_active:
            logger.warning(f"Login failed - inactive user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        try:
            access_token = create_access_token(
                data={"sub": user.email, "user_id": str(user.id), "token_type": "access"}, 
                expires_delta=access_token_expires
            )
            
            # For MVP, we'll use the same expiration for refresh token
            # In production, refresh tokens should have longer expiration
            refresh_token_expires = timedelta(days=7)  # 7 days for refresh token
            refresh_token = create_access_token(
                data={"sub": user.email, "user_id": str(user.id), "token_type": "refresh"}, 
                expires_delta=refresh_token_expires
            )
        except Exception as e:
            logger.error(f"Token creation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token generation error"
            )
        
        user_response = UserResponse.from_orm(db_user)
        
        logger.info(f"Successfully logged in user: {form_data.username}")
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_response
        )
    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        # Log and raise any unexpected errors
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.post("/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token"""
    from jose import JWTError
    from app.core.security import verify_token
    
    try:
        payload = verify_token(refresh_token)
        token_type = payload.get("token_type")
        
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from DB to ensure they still exist and are active
        user = await get_user_by_email(db, email)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists or is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": user.email, "user_id": str(user.id), "token_type": "access"}, 
            expires_delta=access_token_expires
        )
        
        # Create new refresh token for next refresh
        refresh_token_expires = timedelta(days=7)
        new_refresh_token = create_access_token(
            data={"sub": user.email, "user_id": str(user.id), "token_type": "refresh"}, 
            expires_delta=refresh_token_expires
        )
        
        user_response = UserResponse.from_orm(user)
        
        logger.info(f"Token refreshed for user: {email}")
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user=user_response
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh error"
        )

@router.get("/auth/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_active_user)):
    """Get current user's information"""
    return current_user