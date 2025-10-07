from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..models import (
    TamanKehati as TamanKehatiModel,
    Provinsi,
    KabupatenKota,
    Kecamatan,
    Desa
)
from ..schemas.taman_kehati import (
    TamanKehatiCreate,
    TamanKehatiUpdate,
    ProvinsiResponse,
    KabupatenKotaResponse,
    KecamatanResponse,
    DesaResponse
)
from typing import List, Optional
from uuid import UUID
from app.utils.logging_config import get_logger
from app.audit.utils import log_audit_entry

logger = get_logger(__name__)

async def get_taman_kehati(db: AsyncSession, taman_id: int) -> Optional[TamanKehatiModel]:
    """Get a Taman Kehati by ID"""
    logger.info(f"Fetching Taman Kehati with ID: {taman_id}")
    result = await db.execute(
        select(TamanKehatiModel)
        .options(
            selectinload(TamanKehatiModel.provinsi),
            selectinload(TamanKehatiModel.kabupatenKota),
            selectinload(TamanKehatiModel.kecamatan),
            selectinload(TamanKehatiModel.desa),
            selectinload(TamanKehatiModel.zonas),
            selectinload(TamanKehatiModel.koleksis),
            selectinload(TamanKehatiModel.medias),
            selectinload(TamanKehatiModel.artikels),
            selectinload(TamanKehatiModel.createdByUser),
            selectinload(TamanKehatiModel.updatedByUser)
        )
        .filter(TamanKehatiModel.id == taman_id)
    )
    taman = result.scalars().first()
    if taman:
        logger.debug(f"Successfully retrieved Taman Kehati: {taman.namaResmi}")
    else:
        logger.warning(f"Taman Kehati not found with ID: {taman_id}")
    return taman

async def get_tamans_kehati(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[TamanKehatiModel]:
    """Get a list of Taman Kehati"""
    logger.info(f"Fetching Taman Kehati list with skip={skip}, limit={limit}")
    result = await db.execute(
        select(TamanKehatiModel)
        .options(
            selectinload(TamanKehatiModel.provinsi),
            selectinload(TamanKehatiModel.kabupatenKota),
            selectinload(TamanKehatiModel.koleksis)
        )
        .offset(skip)
        .limit(limit)
    )
    tamans = result.scalars().all()
    logger.debug(f"Retrieved {len(tamans)} Taman Kehati records")
    return tamans

async def create_taman_kehati(
    db: AsyncSession, 
    taman: TamanKehatiCreate,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> TamanKehatiModel:
    """Create a new Taman Kehati"""
    logger.info(f"Creating new Taman Kehati: {taman.namaResmi}")
    db_taman = TamanKehatiModel(**taman.dict())
    db.add(db_taman)
    await db.flush()  # Use flush to get the ID before committing
    
    # Log audit entry
    await log_audit_entry(
        db, 
        user_id=current_user_id, 
        action="CREATE", 
        table_name="taman_kehati", 
        record_id=db_taman.id,
        new_data=taman.dict(),
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    await db.commit()
    await db.refresh(db_taman)
    logger.info(f"Successfully created Taman Kehati with ID: {db_taman.id}")
    return db_taman

async def update_taman_kehati(
    db: AsyncSession, 
    taman_id: int, 
    taman: TamanKehatiUpdate,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[TamanKehatiModel]:
    """Update a Taman Kehati"""
    logger.info(f"Updating Taman Kehati with ID: {taman_id}")
    result = await db.execute(
        select(TamanKehatiModel).filter(TamanKehatiModel.id == taman_id)
    )
    db_taman = result.scalars().first()
    
    if not db_taman:
        logger.warning(f"Taman Kehati not found for update with ID: {taman_id}")
        return None
    
    # Capture old data for audit
    old_data = {
        "id": db_taman.id,
        "kode": db_taman.kode,
        "nama_resmi": db_taman.nama_resmi,
        "alamat": db_taman.alamat,
        "luas": float(db_taman.luas) if db_taman.luas else None,
        "tipe_taman": db_taman.tipe_taman.value if hasattr(db_taman.tipe_taman, 'value') else str(db_taman.tipe_taman),
        "tanggal_penetapan": str(db_taman.tanggal_penetapan) if db_taman.tanggal_penetapan else None,
        "deskripsi": db_taman.deskripsi,
        "provinsi_id": db_taman.provinsi_id,
        "kabupaten_kota_id": db_taman.kabupaten_kota_id,
        "kecamatan_id": db_taman.kecamatan_id,
        "desa_id": db_taman.desa_id,
        "latitude": float(db_taman.latitude) if db_taman.latitude else None,
        "longitude": float(db_taman.longitude) if db_taman.longitude else None,
        "status": db_taman.status.value if hasattr(db_taman.status, 'value') else str(db_taman.status),
        "created_at": str(db_taman.created_at),
        "updated_at": str(db_taman.updated_at)
    }
    
    update_data = taman.dict(exclude_unset=True)
    logger.debug(f"Updating Taman Kehati {taman_id} with data: {update_data}")
    for field, value in update_data.items():
        setattr(db_taman, field, value)
    
    await db.commit()
    await db.refresh(db_taman)
    
    # Log audit entry
    await log_audit_entry(
        db, 
        user_id=current_user_id, 
        action="UPDATE", 
        table_name="taman_kehati", 
        record_id=db_taman.id,
        old_data=old_data,
        new_data={**old_data, **update_data},
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    logger.info(f"Successfully updated Taman Kehati with ID: {taman_id}")
    return db_taman

async def delete_taman_kehati(
    db: AsyncSession, 
    taman_id: int,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """Delete a Taman Kehati"""
    logger.info(f"Deleting Taman Kehati with ID: {taman_id}")
    result = await db.execute(
        select(TamanKehatiModel).filter(TamanKehatiModel.id == taman_id)
    )
    db_taman = result.scalars().first()
    
    if not db_taman:
        logger.warning(f"Taman Kehati not found for deletion with ID: {taman_id}")
        return False
    
    # Capture old data for audit
    old_data = {
        "id": db_taman.id,
        "kode": db_taman.kode,
        "nama_resmi": db_taman.nama_resmi,
        "alamat": db_taman.alamat,
        "luas": float(db_taman.luas) if db_taman.luas else None,
        "tipe_taman": db_taman.tipe_taman.value if hasattr(db_taman.tipe_taman, 'value') else str(db_taman.tipe_taman),
        "tanggal_penetapan": str(db_taman.tanggal_penetapan) if db_taman.tanggal_penetapan else None,
        "deskripsi": db_taman.deskripsi,
        "provinsi_id": db_taman.provinsi_id,
        "kabupaten_kota_id": db_taman.kabupaten_kota_id,
        "kecamatan_id": db_taman.kecamatan_id,
        "desa_id": db_taman.desa_id,
        "latitude": float(db_taman.latitude) if db_taman.latitude else None,
        "longitude": float(db_taman.longitude) if db_taman.longitude else None,
        "status": db_taman.status.value if hasattr(db_taman.status, 'value') else str(db_taman.status),
        "created_at": str(db_taman.created_at),
        "updated_at": str(db_taman.updated_at)
    }
    
    await db.delete(db_taman)
    await db.flush()  # Use flush to delete before logging
    
    # Log audit entry
    await log_audit_entry(
        db, 
        user_id=current_user_id, 
        action="DELETE", 
        table_name="taman_kehati", 
        record_id=db_taman.id,
        old_data=old_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    await db.commit()
    logger.info(f"Successfully deleted Taman Kehati with ID: {taman_id}")
    return True


# Reference Geography Functions
async def get_provinsi_list(db: AsyncSession) -> List[ProvinsiResponse]:
    """Get list of all provinces"""
    logger.info("Fetching all provinces")
    result = await db.execute(
        select(Provinsi).order_by(Provinsi.nama)
    )
    provinsi_list = result.scalars().all()
    logger.debug(f"Retrieved {len(provinsi_list)} provinces")
    return [ProvinsiResponse.from_orm(p) for p in provinsi_list]


async def get_provinsi(db: AsyncSession, provinsi_id: int) -> Optional[Provinsi]:
    """Get a specific province by ID"""
    logger.info(f"Fetching province with ID: {provinsi_id}")
    result = await db.execute(
        select(Provinsi).filter(Provinsi.id == provinsi_id)
    )
    provinsi = result.scalars().first()
    if provinsi:
        logger.debug(f"Successfully retrieved province: {provinsi.nama}")
    else:
        logger.warning(f"Province not found with ID: {provinsi_id}")
    return provinsi


async def get_kabupaten_kota_by_provinsi(db: AsyncSession, provinsi_id: int) -> List[KabupatenKotaResponse]:
    """Get list of kabupaten/kota by provinsi ID"""
    logger.info(f"Fetching kabupaten-kota for provinsi ID: {provinsi_id}")
    result = await db.execute(
        select(KabupatenKota)
        .filter(KabupatenKota.provinsi_id == provinsi_id)
        .order_by(KabupatenKota.nama)
    )
    kabupaten_list = result.scalars().all()
    logger.debug(f"Retrieved {len(kabupaten_list)} kabupaten-kota for provinsi {provinsi_id}")
    return [KabupatenKotaResponse.from_orm(k) for k in kabupaten_list]


async def get_kecamatan_by_kabupaten(db: AsyncSession, kabupaten_kota_id: int) -> List[KecamatanResponse]:
    """Get list of kecamatan by kabupaten/kota ID"""
    logger.info(f"Fetching kecamatan for kabupaten-kota ID: {kabupaten_kota_id}")
    result = await db.execute(
        select(Kecamatan)
        .filter(Kecamatan.kabupaten_kota_id == kabupaten_kota_id)
        .order_by(Kecamatan.nama)
    )
    kecamatan_list = result.scalars().all()
    logger.debug(f"Retrieved {len(kecamatan_list)} kecamatan for kabupaten-kota {kabupaten_kota_id}")
    return [KecamatanResponse.from_orm(k) for k in kecamatan_list]


async def get_desa_by_kecamatan(db: AsyncSession, kecamatan_id: int) -> List[DesaResponse]:
    """Get list of desa by kecamatan ID"""
    logger.info(f"Fetching desa for kecamatan ID: {kecamatan_id}")
    result = await db.execute(
        select(Desa)
        .filter(Desa.kecamatan_id == kecamatan_id)
        .order_by(Desa.nama)
    )
    desa_list = result.scalars().all()
    logger.debug(f"Retrieved {len(desa_list)} desa for kecamatan {kecamatan_id}")
    return [DesaResponse.from_orm(d) for d in desa_list]