import asyncio
from sqlalchemy import text
from app.database import engine, Base

async def create_tables():
    print("Creating database tables...")
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())