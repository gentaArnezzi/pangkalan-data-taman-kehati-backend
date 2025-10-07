from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from app.database import get_db
from app.auth.utils import get_current_active_user, get_current_admin
from app.crud.koleksi_tumbuhan import get_koleksis_tumbuhan
from app.utils.data_standards import create_dwc_export, model_to_geojson_collection

router = APIRouter()

@router.get("/export/dwc")
async def export_dwc_data(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return", le=10000),
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Export plant collection data in Darwin Core format
    """
    koleksi_list = await get_koleksis_tumbuhan(db, skip=skip, limit=limit)
    
    # Convert to dictionaries for processing
    koleksi_dicts = []
    for koleksi in koleksi_list:
        koleksi_dict = {
            'id': koleksi.id,
            'nomor_koleksi': koleksi.nomor_koleksi,
            'nama_ilmiah': koleksi.nama_ilmiah,
            'genus': koleksi.genus,
            'spesies': koleksi.spesies,
            'author': koleksi.author,
            'nama_lokal_daerah': koleksi.nama_lokal_daerah,
            'nama_umum_nasional': koleksi.nama_umum_nasional,
            'latitude_taman': float(koleksi.latitude_taman) if koleksi.latitude_taman else None,
            'longitude_taman': float(koleksi.longitude_taman) if koleksi.longitude_taman else None,
            'ketinggian_taman': koleksi.ketinggian_taman,
            'status_endemik': koleksi.status_endemik,
            'taman_kehati_id': koleksi.taman_kehati_id,
            'tanggal_penanaman': koleksi.tanggal_penanaman,
            'status': koleksi.status,
        }
        koleksi_dicts.append(koleksi_dict)
    
    # Create DwC export
    dwc_data = create_dwc_export(koleksi_dicts)
    
    # Return as JSON
    return dwc_data


@router.get("/export/geojson")
async def export_geojson_data(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return", le=10000),
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Export plant collection data in GeoJSON format
    """
    koleksi_list = await get_koleksis_tumbuhan(db, skip=skip, limit=limit)
    
    # Convert to dictionaries for processing
    koleksi_dicts = []
    for koleksi in koleksi_list:
        koleksi_dict = {
            'id': koleksi.id,
            'nomor_koleksi': koleksi.nomor_koleksi,
            'nama_ilmiah': koleksi.nama_ilmiah,
            'genus': koleksi.genus,
            'spesies': koleksi.spesies,
            'author': koleksi.author,
            'nama_lokal_daerah': koleksi.nama_lokal_daerah,
            'nama_umum_nasional': koleksi.nama_umum_nasional,
            'latitude_taman': float(koleksi.latitude_taman) if koleksi.latitude_taman else None,
            'longitude_taman': float(koleksi.longitude_taman) if koleksi.longitude_taman else None,
            'ketinggian_taman': koleksi.ketinggian_taman,
            'status_endemik': koleksi.status_endemik,
            'taman_kehati_id': koleksi.taman_kehati_id,
            'tanggal_penanaman': koleksi.tanggal_penanaman,
            'status': koleksi.status,
        }
        koleksi_dicts.append(koleksi_dict)
    
    # Create GeoJSON export
    geojson_data = model_to_geojson_collection(koleksi_dicts, include_sensitivity_masking=True)
    
    return geojson_data