#!/usr/bin/env python3
"""
Script untuk menambahkan user pertama ke database
"""
import asyncio
import hashlib
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Password hashing context with bcrypt_sha256 to handle passwords > 72 bytes
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],  # new first, old second for backward compatibility
    deprecated="auto"
)

# Database URL (gunakan dari environment)
DATABASE_URL = os.getenv("ASYNC_DATABASE_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL atau ASYNC_DATABASE_URL harus diatur di .env")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,  # Recycle connections every 5 minutes
    connect_args={
        "application_name": "taman-kehati-init",
    }
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def create_user(email: str, password: str, nama: str, role: str = "super_admin"):
    """Create a new user in the database"""
    async with AsyncSessionLocal() as session:
        try:
            # Hash the password directly with bcrypt's built-in length check
            hashed_password = pwd_context.hash(password)
            
            # Insert user into database
            query = text("""
                INSERT INTO users (email, password, nama, role, is_active, created_at, updated_at)
                VALUES (:email, :password, :nama, :role, :is_active, NOW(), NOW())
                RETURNING id
            """)
            
            result = await session.execute(query, {
                "email": email,
                "password": hashed_password,
                "nama": nama,
                "role": role,
                "is_active": True
            })
            
            user_id = result.fetchone()[0]
            await session.commit()
            
            print(f"User created successfully with ID: {user_id}")
            return user_id
            
        except Exception as e:
            await session.rollback()
            print(f"Error creating user: {str(e)}")
            raise

async def main():
    print("Creating initial user...")
    
    # Create a test user
    email = "admin@tamankehati.com"
    password = "admin123"  # Password yang lebih pendek agar tidak melebihi 72 byte
    nama = "Admin Taman Kehati"
    
    user_id = await create_user(email, password, nama, "super_admin")
    print(f"Successfully created user: {email}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Role: super_admin")

if __name__ == "__main__":
    asyncio.run(main())