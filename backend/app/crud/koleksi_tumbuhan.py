from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models import KoleksiTumbuhan as KoleksiTumbuhanModel
from app.schemas.koleksi_tumbuhan import KoleksiTumbuhanCreate, KoleksiTumbuhanUpdate
from typing import List, Optional

async def get_koleksi_tumbuhan(db: AsyncSession, koleksi_id: int) -> Optional[KoleksiTumbuhanModel]:
    """Get a plant collection by ID"""
    result = await db.execute(
        select(KoleksiTumbuhanModel)
        .options(
            selectinload(KoleksiTumbuhanModel.taman),
            selectinload(KoleksiTumbuhanModel.zona),
            selectinload(KoleksiTumbuhanModel.medias),
            selectinload(KoleksiTumbuhanModel.asalDesa),
            selectinload(KoleksiTumbuhanModel.asalKecamatan),
            selectinload(KoleksiTumbuhanModel.asalKabupaten),
            selectinload(KoleksiTumbuhanModel.asalProvinsi)
        )
        .filter(KoleksiTumbuhanModel.id == koleksi_id)
    )
    return result.scalars().first()

async def get_koleksis_tumbuhan(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[KoleksiTumbuhanModel]:
    """Get a list of plant collections"""
    result = await db.execute(
        select(KoleksiTumbuhanModel)
        .options(
            selectinload(KoleksiTumbuhanModel.taman),
            selectinload(KoleksiTumbuhanModel.zona)
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_koleksi_tumbuhan(db: AsyncSession, koleksi: KoleksiTumbuhanCreate) -> KoleksiTumbuhanModel:
    """Create a new plant collection"""
    db_koleksi = KoleksiTumbuhanModel(**koleksi.dict())
    db.add(db_koleksi)
    await db.commit()
    await db.refresh(db_koleksi)
    return db_koleksi

async def update_koleksi_tumbuhan(db: AsyncSession, koleksi_id: int, koleksi: KoleksiTumbuhanUpdate) -> Optional[KoleksiTumbuhanModel]:
    """Update a plant collection"""
    result = await db.execute(
        select(KoleksiTumbuhanModel).filter(KoleksiTumbuhanModel.id == koleksi_id)
    )
    db_koleksi = result.scalars().first()
    
    if not db_koleksi:
        return None
    
    update_data = koleksi.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_koleksi, field, value)
    
    await db.commit()
    await db.refresh(db_koleksi)
    return db_koleksi

async def delete_koleksi_tumbuhan(db: AsyncSession, koleksi_id: int) -> bool:
    """Delete a plant collection"""
    result = await db.execute(
        select(KoleksiTumbuhanModel).filter(KoleksiTumbuhanModel.id == koleksi_id)
    )
    db_koleksi = result.scalars().first()
    
    if not db_koleksi:
        return False
    
    await db.delete(db_koleksi)
    await db.commit()
    return True