from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.database import get_db
from app.schemas.taman_kehati import (
    TamanKehatiCreate, 
    TamanKehatiUpdate, 
    TamanKehatiResponse,
    TamanKehatiGeoResponse,
    TamanKehatiStatsResponse
)
from app.auth.utils import get_current_active_user, get_current_admin
from app.crud.taman_kehati import (
    get_taman_kehati, 
    get_tamans_kehati, 
    create_taman_kehati as create_taman,
    update_taman_kehati,
    delete_taman_kehati
)
from app.utils.geo_masking import mask_coordinates
from app.utils.logging_config import get_logger
from app.models import StatusPublikasiEnum
from sqlalchemy import text, func

router = APIRouter()
logger = get_logger(__name__)

@router.get("/", response_model=List[TamanKehatiResponse])
async def read_tamans_kehati(
    page: int = 1, 
    size: int = 20,
    sort: Optional[str] = None,
    q: Optional[str] = None,
    status: Optional[StatusPublikasiEnum] = None,
    provinsi_id: Optional[int] = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of all Taman Kehati with pagination, filtering, and search"""
    # Convert page/size to skip/limit for now (will implement proper pagination later)
    skip = (page - 1) * size
    limit = size

    logger.info(f"Fetching Taman Kehati list - user: {current_user.email}, page: {page}, size: {size}, sort: {sort}, q: {q}, status: {status}, provinsi_id: {provinsi_id}")

    # Import necessary modules
    from sqlalchemy import or_, func
    from app.models import TamanKehati as TamanKehatiModel
    from sqlalchemy.future import select
    from sqlalchemy.orm import selectinload
    
    # Build query with optional filters
    query = select(TamanKehatiModel).options(selectinload(TamanKehatiModel.provinsi)).offset(skip).limit(limit)
    
    # Add filters if provided
    filters = []
    
    if status:
        filters.append(TamanKehatiModel.status == status)
    
    if provinsi_id:
        filters.append(TamanKehatiModel.provinsi_id == provinsi_id)
        
    if q:
        filters.append(
            or_(
                TamanKehatiModel.nama_resmi.ilike(f"%{q}%"),
                TamanKehatiModel.alamat.ilike(f"%{q}%"),
                TamanKehatiModel.deskripsi.ilike(f"%{q}%")
            )
        )
    
    if filters:
        query = query.filter(*filters)
        
    # Apply sorting if specified
    if sort:
        # Handle sorting - could be field names, with optional '-' prefix for descending
        sort_fields = sort.split(',')
        for field in sort_fields:
            field = field.strip()
            if field.startswith('-'):
                field_name = field[1:]
                # Apply descending sort
                if hasattr(TamanKehatiModel, field_name):
                    query = query.order_by(getattr(TamanKehatiModel, field_name).desc())
            else:
                # Apply ascending sort
                if hasattr(TamanKehatiModel, field):
                    query = query.order_by(getattr(TamanKehatiModel, field))
    
    # Execute query
    result = await db.execute(query)
    tamans = result.scalars().all()
    
    # Apply geo-masking for non-admin users
    if current_user.role not in ["super_admin", "admin_taman"]:
        for taman in tamans:
            if taman.latitude and taman.longitude:
                taman.latitude, taman.longitude = mask_coordinates(
                    taman.latitude, 
                    taman.longitude, 
                    user_role=current_user.role
                )
                logger.debug(f"Applied geo-masking for user {current_user.email} on Taman Kehati {taman.id}")
    
    logger.info(f"Successfully returned {len(tamans)} Taman Kehati records")
    return [TamanKehatiResponse.from_orm(t) for t in tamans]

@router.get("/{taman_id}", response_model=TamanKehatiResponse)
async def read_taman_kehati(
    taman_id: int, 
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific Taman Kehati by ID"""
    logger.info(f"Fetching Taman Kehati with ID {taman_id} for user: {current_user.email}")
    taman = await get_taman_kehati(db, taman_id)
    if not taman:
        logger.warning(f"Taman Kehati with ID {taman_id} not found for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taman Kehati not found"
        )
    
    # Apply geo-masking for non-admin users
    if current_user.role not in ["super_admin", "admin_taman"]:
        if taman.latitude and taman.longitude:
            taman.latitude, taman.longitude = mask_coordinates(
                taman.latitude, 
                taman.longitude, 
                user_role=current_user.role
            )
            logger.debug(f"Applied geo-masking for user {current_user.email} on Taman Kehati {taman.id}")
    
    logger.info(f"Successfully returned Taman Kehati: {taman.namaResmi}")
    return TamanKehatiResponse.from_orm(taman)


@router.get("/{taman_id}/geo", response_model=TamanKehatiGeoResponse)
async def read_taman_kehati_geo(
    taman_id: int, 
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Taman Kehati geometry as GeoJSON FeatureCollection"""
    logger.info(f"Fetching Taman Kehati geometry with ID {taman_id} for user: {current_user.email}")
    
    # Get the full taman with geometry
    from app.models import TamanKehati as TamanKehatiModel
    from sqlalchemy.future import select
    
    result = await db.execute(
        select(TamanKehatiModel)
        .filter(TamanKehatiModel.id == taman_id)
    )
    taman = result.scalars().first()
    
    if not taman:
        logger.warning(f"Taman Kehati with ID {taman_id} not found for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taman Kehati not found"
        )
    
    # Prepare GeoJSON feature
    features = []
    
    # Add point feature for the center coordinates
    if taman.latitude and taman.longitude:
        # Apply geo-masking for non-admin users
        lat, lng = taman.latitude, taman.longitude
        if current_user.role not in ["super_admin", "admin_taman"]:
            lat, lng = mask_coordinates(
                taman.latitude, 
                taman.longitude, 
                user_role=current_user.role
            )
            logger.debug(f"Applied geo-masking for user {current_user.email} on Taman Kehati {taman.id}")
        
        point_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lng), float(lat)]
            },
            "properties": {
                "id": taman.id,
                "nama": taman.nama_resmi,
                "type": "center_point"
            }
        }
        features.append(point_feature)
    
    # Add polygon feature for the boundary
    if taman.batas_area:
        # Convert WKB to GeoJSON using ST_AsGeoJSON
        polygon_result = await db.execute(
            text("SELECT ST_AsGeoJSON(:batas_area) as geom"),
            {"batas_area": taman.batas_area}
        )
        polygon_row = polygon_result.fetchone()
        if polygon_row:
            geometry = json.loads(polygon_row.geom)
            polygon_feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "id": taman.id,
                    "nama": taman.nama_resmi,
                    "type": "boundary"
                }
            }
            features.append(polygon_feature)
    
    geo_response = TamanKehatiGeoResponse(features=features)
    logger.info(f"Successfully returned geometry for Taman Kehati: {taman.nama_resmi}")
    return geo_response


@router.get("/{taman_id}/stats", response_model=TamanKehatiStatsResponse)
async def read_taman_kehati_stats(
    taman_id: int, 
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Taman Kehati statistics"""
    logger.info(f"Fetching Taman Kehati stats with ID {taman_id} for user: {current_user.email}")
    
    # Count collections for this taman
    from app.models import KoleksiTumbuhan
    from sqlalchemy import func
    
    koleksi_result = await db.execute(
        select(func.count(KoleksiTumbuhan.id))
        .filter(KoleksiTumbuhan.taman_kehati_id == taman_id)
    )
    koleksi_count = koleksi_result.scalar_one_or_none() or 0
    
    # For now, hardcoding the other stats - in a real implementation, 
    # you would need to implement article counting and view counting
    stats = TamanKehatiStatsResponse(
        koleksi_count=koleksi_count,
        artikel_count=0,  # Placeholder
        views_7d=0,  # Placeholder
        views_30d=0  # Placeholder
    )
    
    logger.info(f"Successfully returned stats for Taman Kehati {taman_id}: {stats}")
    return stats


@router.get("/near", response_model=List[TamanKehatiResponse])
async def read_tamans_near(
    lat: float,
    lng: float, 
    radius_m: float = 10000,  # 10km default
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Find Taman Kehati near the given coordinates within radius (in meters)"""
    logger.info(f"Finding Taman Kehati near lat:{lat}, lng:{lng}, radius:{radius_m}m - user: {current_user.email}")
    
    # Use PostGIS ST_DWithin to find parks within radius
    # First, convert the input coordinates to a point geometry
    from sqlalchemy import text
    
    result = await db.execute(
        text("""
            SELECT *, 
                   ST_Distance(
                       koordinat, 
                       ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)
                   ) AS distance
            FROM taman_kehati
            WHERE ST_DWithin(
                koordinat, 
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), 
                :radius
            )
            ORDER BY distance
            LIMIT 20
        """),
        {"lng": lng, "lat": lat, "radius": radius_m}
    )
    
    tamans = []
    for row in result:
        # Create TamanKehati model from row
        from app.models import TamanKehati as TamanKehatiModel
        from sqlalchemy.orm import class_mapper
        
        # Create a TamanKehati instance from the row data
        taman_data = {}
        for column in class_mapper(TamanKehatiModel).columns:
            if hasattr(row, column.name):
                taman_data[column.name] = getattr(row, column.name)
        
        taman = TamanKehatiModel(**taman_data)
        
        # Apply geo-masking for non-admin users
        if current_user.role not in ["super_admin", "admin_taman"]:
            if taman.latitude and taman.longitude:
                taman.latitude, taman.longitude = mask_coordinates(
                    taman.latitude, 
                    taman.longitude, 
                    user_role=current_user.role
                )
                logger.debug(f"Applied geo-masking for user {current_user.email} on Taman Kehati {taman.id}")
        
        tamans.append(TamanKehatiResponse.from_orm(taman))
    
    logger.info(f"Successfully returned {len(tamans)} Taman Kehati near the specified coordinates")
    return tamans

@router.post("/", response_model=TamanKehatiResponse)
async def create_taman_kehati(
    taman: TamanKehatiCreate,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new Taman Kehati (admin only)"""
    logger.info(f"Creating new Taman Kehati by admin user: {current_user.email}")
    db_taman = await create_taman(db, taman, current_user_id=current_user.id)
    logger.info(f"Successfully created Taman Kehati '{db_taman.namaResmi}' with ID: {db_taman.id}")
    return db_taman

@router.put("/{taman_id}", response_model=TamanKehatiResponse)
async def update_taman_kehati(
    taman_id: int,
    taman: TamanKehatiUpdate,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a Taman Kehati (admin only)"""
    logger.info(f"Updating Taman Kehati ID {taman_id} by admin user: {current_user.email}")
    db_taman = await update_taman_kehati(db, taman_id, taman, current_user_id=current_user.id)
    if not db_taman:
        logger.warning(f"Failed to update Taman Kehati ID {taman_id} - not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taman Kehati not found"
        )
    logger.info(f"Successfully updated Taman Kehati '{db_taman.namaResmi}' with ID: {db_taman.id}")
    return db_taman

@router.delete("/{taman_id}")
async def delete_taman_kehati(
    taman_id: int,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a Taman Kehati (admin only)"""
    logger.info(f"Deleting Taman Kehati ID {taman_id} by admin user: {current_user.email}")
    success = await delete_taman_kehati(db, taman_id, current_user_id=current_user.id)
    if not success:
        logger.warning(f"Failed to delete Taman Kehati ID {taman_id} - not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taman Kehati not found"
        )
    logger.info(f"Successfully deleted Taman Kehati ID {taman_id}")
    return {"message": "Taman Kehati deleted successfully"}