from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

from app.settings import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with proper timezone-aware datetime
    
    Args:
        data: Dictionary containing the claims to encode in the token
        expires_delta: Optional timedelta for token expiration (defaults to settings value)
    
    Returns:
        Encoded JWT token as string
    """
    to_encode = data.copy()
    
    # Use timezone-aware datetime to avoid deprecation warnings
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify a JWT token and return its payload
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded token payload as dictionary
        
    Raises:
        JWTError: If token is invalid or expired
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])