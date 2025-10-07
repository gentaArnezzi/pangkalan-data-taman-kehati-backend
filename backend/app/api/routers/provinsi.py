from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ...database import get_db
from ...schemas.taman_kehati import (
    ProvinsiResponse, 
    KabupatenKotaResponse, 
    KecamatanResponse, 
    DesaResponse
)
from ...auth.utils import get_current_active_user
from ...crud.taman_kehati import (
    get_provinsi,
    get_provinsi_list,
    get_kabupaten_kota_by_provinsi,
    get_kecamatan_by_kabupaten,
    get_desa_by_kecamatan
)
from ...utils.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.get("/provinsi", response_model=List[ProvinsiResponse])
async def read_provinsi(
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of all provinces"""
    logger.info(f"Fetching provinces - user: {current_user.email}")
    provinsi_list = await get_provinsi_list(db)
    logger.info(f"Successfully returned {len(provinsi_list)} provinces")
    return provinsi_list


@router.get("/kabupaten-kota", response_model=List[KabupatenKotaResponse])
async def read_kabupaten_kota(
    provinsi_id: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of kabupaten/kota filtered by provinsi"""
    logger.info(f"Fetching kabupaten-kota for provinsi {provinsi_id} - user: {current_user.email}")
    kabupaten_list = await get_kabupaten_kota_by_provinsi(db, provinsi_id)
    logger.info(f"Successfully returned {len(kabupaten_list)} kabupaten-kota")
    return kabupaten_list


@router.get("/kecamatan", response_model=List[KecamatanResponse])
async def read_kecamatan(
    kabupaten_kota_id: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of kecamatan filtered by kabupaten/kota"""
    logger.info(f"Fetching kecamatan for kabupaten-kota {kabupaten_kota_id} - user: {current_user.email}")
    kecamatan_list = await get_kecamatan_by_kabupaten(db, kabupaten_kota_id)
    logger.info(f"Successfully returned {len(kecamatan_list)} kecamatan")
    return kecamatan_list


@router.get("/desa", response_model=List[DesaResponse])
async def read_desa(
    kecamatan_id: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of desa filtered by kecamatan"""
    logger.info(f"Fetching desa for kecamatan {kecamatan_id} - user: {current_user.email}")
    desa_list = await get_desa_by_kecamatan(db, kecamatan_id)
    logger.info(f"Successfully returned {len(desa_list)} desa")
    return desa_list