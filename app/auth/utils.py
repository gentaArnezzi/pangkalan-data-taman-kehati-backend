from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from app.settings import settings
from ..models import User as UserModel, UserRoleEnum
from ..schemas.users import UserResponse

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Password hashing context with bcrypt_sha256 to handle passwords > 72 bytes
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],  # new first, old second for backward compatibility
    deprecated="auto"
)

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None

class UserInDB(BaseModel):
    id: str
    email: str
    nama: str
    role: str
    is_active: bool
    taman_kehati_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    # Truncate password to 72 bytes if longer to prevent bcrypt errors
    truncated_password = plain_password[:72] if len(plain_password.encode('utf-8')) > 72 else plain_password
    return pwd_context.verify(truncated_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt_sha256 (no 72-byte limit)"""
    # Truncate password to 72 bytes if longer to prevent bcrypt errors during hash creation
    truncated_password = password[:72] if len(password.encode('utf-8')) > 72 else password
    return pwd_context.hash(truncated_password)

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user by email and password"""
    result = await db.execute(select(UserModel).filter(UserModel.email == email))
    user = result.scalars().first()
    
    if not user or not verify_password(password, user.password):
        return None
    
    # Handle the role field properly - it could be an enum or string from the database
    role_value = user.role.value if hasattr(user.role, 'value') else user.role
    
    return UserInDB(
        id=str(user.id),
        email=user.email,
        nama=user.nama,
        role=role_value,
        is_active=user.is_active,
        taman_kehati_id=user.taman_kehati_id
    )

def create_access_token_with_datetime(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token - deprecated, use core.security.create_access_token instead"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> UserInDB:
    """Get the current user from the token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(UserModel).filter(UserModel.email == token_data.email))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    
    # Handle the role field properly - it could be an enum or string from the database
    role_value = user.role.value if hasattr(user.role, 'value') else user.role
    
    return UserInDB(
        id=str(user.id),
        email=user.email,
        nama=user.nama,
        role=role_value,
        is_active=user.is_active,
        taman_kehati_id=user.taman_kehati_id
    )

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_role_checker(required_roles: list):
    """Create a role checker function for dependency injection"""
    def role_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: required roles {required_roles}, user has role {current_user.role}"
            )
        return current_user
    return role_checker

# Predefined role checkers
get_current_admin = get_role_checker(["super_admin", "admin_taman"])
get_current_super_admin = get_role_checker(["super_admin"])


async def check_taman_access(
    db: AsyncSession,
    current_user: UserInDB,
    taman_kehati_id: int
) -> bool:
    """
    Check if the current user has access to a specific taman.
    super_admin: access to all tamans
    admin_taman: access only to their assigned taman
    viewer: read access to published content
    """
    if current_user.role == "super_admin":
        return True
    
    if current_user.role == "admin_taman":
        # Check if this taman belongs to the user's assigned taman
        if current_user.taman_kehati_id and current_user.taman_kehati_id == taman_kehati_id:
            return True
        else:
            return False
    
    # For viewers or other roles, return False for write operations
    # This function is typically used for write operations
    return False


def get_taman_admin():
    """Dependency that allows only users with access to a specific taman"""
    async def taman_admin_checker(
        current_user: UserInDB = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> UserInDB:
        if current_user.role not in ["super_admin", "admin_taman"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: required admin role"
            )
        return current_user
    return taman_admin_checker