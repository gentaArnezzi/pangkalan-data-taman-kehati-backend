from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.database import get_db
from app.schemas.koleksi_tumbuhan import (
    KoleksiTumbuhanCreate, 
    KoleksiTumbuhanUpdate, 
    KoleksiTumbuhanResponse,
    KoleksiTumbuhanStatsResponse,
    KoleksiTumbuhanStatsGroup
)
from app.auth.utils import get_current_active_user, get_current_admin
from app.crud.koleksi_tumbuhan import (
    get_koleksi_tumbuhan, 
    get_koleksis_tumbuhan, 
    create_koleksi_tumbuhan as create_koleksi,
    update_koleksi_tumbuhan,
    delete_koleksi_tumbuhan
)
from app.utils.geo_masking import mask_coordinates, PRECISION_LEVELS
from app.utils.logging_config import get_logger
from sqlalchemy import text, func
from app.models import StatusPublikasiEnum, StatusEndemikEnum

router = APIRouter()

router = APIRouter()
logger = get_logger(__name__)

@router.get("/", response_model=List[KoleksiTumbuhanResponse])
async def read_koleksis_tumbuhan(
    page: int = 1, 
    size: int = 20,
    sort: Optional[str] = None,
    q: Optional[str] = None,
    fields: Optional[str] = None,
    include: Optional[str] = None,
    taman_kehati_id: Optional[int] = None,
    zona_id: Optional[int] = None,
    status: Optional[StatusPublikasiEnum] = None,
    status_endemik: Optional[StatusEndemikEnum] = None,
    genus: Optional[str] = None,
    spesies: Optional[str] = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of plant collections with advanced filtering, pagination, and search"""
    skip = (page - 1) * size
    limit = size

    logger.info(f"Fetching plant collections - user: {current_user.email}, page: {page}, size: {size}, taman_kehati_id: {taman_kehati_id}, zona_id: {zona_id}")

    # Import necessary modules
    from sqlalchemy import or_, and_
    from app.models import KoleksiTumbuhan as KoleksiTumbuhanModel
    from sqlalchemy.future import select
    
    # Build query with optional filters
    query = select(KoleksiTumbuhanModel).offset(skip).limit(limit)
    
    # Add filters if provided
    filters = []
    
    if status:
        filters.append(KoleksiTumbuhanModel.status == status)
    
    if taman_kehati_id:
        filters.append(KoleksiTumbuhanModel.taman_kehati_id == taman_kehati_id)
        
    if zona_id:
        filters.append(KoleksiTumbuhanModel.zona_id == zona_id)
        
    if status_endemik:
        filters.append(KoleksiTumbuhanModel.status_endemik == status_endemik)
        
    if genus:
        filters.append(KoleksiTumbuhanModel.genus.ilike(f"%{genus}%"))
        
    if spesies:
        filters.append(KoleksiTumbuhanModel.spesies.ilike(f"%{spesies}%"))
        
    if q:
        filters.append(
            or_(
                KoleksiTumbuhanModel.nama_ilmiah.ilike(f"%{q}%"),
                KoleksiTumbuhanModel.nama_umum_nasional.ilike(f"%{q}%"),
                KoleksiTumbuhanModel.nama_lokal_daerah.ilike(f"%{q}%"),
                KoleksiTumbuhanModel.bentuk_pohon.ilike(f"%{q}%"),
                KoleksiTumbuhanModel.bentuk_daun.ilike(f"%{q}%")
            )
        )
    
    if filters:
        query = query.filter(and_(*filters))
        
    # Apply sorting if specified
    if sort:
        # Handle sorting - could be field names, with optional '-' prefix for descending
        sort_fields = sort.split(',')
        for field in sort_fields:
            field = field.strip()
            if field.startswith('-'):
                field_name = field[1:]
                # Apply descending sort
                if hasattr(KoleksiTumbuhanModel, field_name):
                    query = query.order_by(getattr(KoleksiTumbuhanModel, field_name).desc())
            else:
                # Apply ascending sort
                if hasattr(KoleksiTumbuhanModel, field):
                    query = query.order_by(getattr(KoleksiTumbuhanModel, field))
    
    # Execute query
    result = await db.execute(query)
    koleksi_list = result.scalars().all()
    
    # Apply geo-masking for non-admin users
    if current_user.role not in ["super_admin", "admin_taman"]:
        for koleksi in koleksi_list:
            # Mask coordinates in the taman
            if koleksi.latitude_taman and koleksi.longitude_taman:
                koleksi.latitude_taman, koleksi.longitude_taman = mask_coordinates(
                    koleksi.latitude_taman, 
                    koleksi.longitude_taman, 
                    user_role=current_user.role,
                    species_type=koleksi.status_endemik  # Use endemism as sensitivity indicator
                )
            
            # Mask coordinates of original location
            if koleksi.latitude_asal and koleksi.longitude_asal:
                koleksi.latitude_asal, koleksi.longitude_asal = mask_coordinates(
                    koleksi.latitude_asal, 
                    koleksi.longitude_asal, 
                    user_role=current_user.role,
                    species_type="sensitive" if koleksi.status_endemik == "endemik" else "common"
                )
    
    logger.info(f"Successfully returned {len(koleksi_list)} plant collections")
    return [KoleksiTumbuhanResponse.from_orm(k) for k in koleksi_list]

@router.get("/{koleksi_id}", response_model=KoleksiTumbuhanResponse)
async def read_koleksi_tumbuhan(
    koleksi_id: int, 
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific plant collection by ID"""
    logger.info(f"Fetching plant collection with ID {koleksi_id} for user: {current_user.email}")
    koleksi = await get_koleksi_tumbuhan(db, koleksi_id)
    if not koleksi:
        logger.warning(f"Plant collection with ID {koleksi_id} not found for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant collection not found"
        )
    
    # Apply geo-masking for non-admin users
    if current_user.role not in ["super_admin", "admin_taman"]:
        # Mask coordinates in the taman
        if koleksi.latitude_taman and koleksi.longitude_taman:
            koleksi.latitude_taman, koleksi.longitude_taman = mask_coordinates(
                koleksi.latitude_taman, 
                koleksi.longitude_taman, 
                user_role=current_user.role,
                species_type=koleksi.status_endemik  # Use endemism as sensitivity indicator
            )
        
        # Mask coordinates of original location
        if koleksi.latitude_asal and koleksi.longitude_asal:
            koleksi.latitude_asal, koleksi.longitude_asal = mask_coordinates(
                koleksi.latitude_asal, 
                koleksi.longitude_asal, 
                user_role=current_user.role,
                species_type="sensitive" if koleksi.status_endemik == "endemik" else "common"
            )
    
    logger.info(f"Successfully returned plant collection: {koleksi.nama_ilmiah}")
    return KoleksiTumbuhanResponse.from_orm(koleksi)

@router.post("/", response_model=KoleksiTumbuhanResponse)
async def create_koleksi_tumbuhan(
    koleksi: KoleksiTumbuhanCreate,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new plant collection (admin only)"""
    db_koleksi = await create_koleksi(db, koleksi)
    return db_koleksi

@router.put("/{koleksi_id}", response_model=KoleksiTumbuhanResponse)
async def update_koleksi_tumbuhan(
    koleksi_id: int,
    koleksi: KoleksiTumbuhanUpdate,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a plant collection (admin only)"""
    db_koleksi = await update_koleksi_tumbuhan(db, koleksi_id, koleksi)
    if not db_koleksi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant collection not found"
        )
    return db_koleksi

@router.get("/{koleksi_id}/media", response_model=List[dict])  # Using dict temporarily
async def read_koleksi_media(
    koleksi_id: int, 
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get media associated with a plant collection"""
    logger.info(f"Fetching media for plant collection ID {koleksi_id} for user: {current_user.email}")
    
    # Import Media model and get media for this collection
    from app.models import Media
    from sqlalchemy.future import select
    
    result = await db.execute(
        select(Media)
        .filter(Media.koleksi_tumbuhan_id == koleksi_id)
    )
    media_list = result.scalars().all()
    
    # Convert to response format
    from app.schemas.media import MediaResponse
    media_responses = [MediaResponse.from_orm(m) for m in media_list]
    
    logger.info(f"Successfully returned {len(media_responses)} media items for collection {koleksi_id}")
    return media_responses


@router.get("/{koleksi_id}/relations", response_model=dict)  # Using dict for now
async def read_koleksi_relations(
    koleksi_id: int, 
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get related collections and articles for a plant collection"""
    logger.info(f"Fetching relations for plant collection ID {koleksi_id} for user: {current_user.email}")
    
    # This is a placeholder implementation - in a real app, you would implement
    # proper relation finding logic
    relations = {
        "terkait": [],  # Related collections
        "artikel_terkait": []  # Related articles
    }
    
    logger.info(f"Successfully returned relations for collection {koleksi_id}")
    return relations


@router.get("/suggest", response_model=List[str])
async def suggest_koleksi(
    q: str, 
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get plant collection suggestions based on search query"""
    logger.info(f"Getting suggestions for query: '{q}' for user: {current_user.email}")
    
    if len(q) < 2:
        return []
    
    from app.models import KoleksiTumbuhan as KoleksiTumbuhanModel
    from sqlalchemy.future import select
    
    # Search in nama_ilmiah, nama_umum_nasional, and nama_lokal_daerah
    result = await db.execute(
        select(KoleksiTumbuhanModel.nama_ilmiah)
        .filter(KoleksiTumbuhanModel.nama_ilmiah.ilike(f"%{q}%"))
        .limit(10)
    )
    
    suggestions = [row[0] for row in result]
    
    logger.info(f"Successfully returned {len(suggestions)} suggestions for query: '{q}'")
    return suggestions


@router.get("/stats", response_model=KoleksiTumbuhanStatsResponse)
async def read_koleksi_stats(
    group_by: str, 
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get plant collection statistics grouped by specified field"""
    logger.info(f"Getting stats grouped by '{group_by}' for user: {current_user.email}")
    
    # Validate group_by parameter
    valid_fields = ["status_endemik", "genus", "taman_kehati_id"]
    if group_by not in valid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid group_by field: {group_by}. Valid options: {valid_fields}"
        )
    
    from app.models import KoleksiTumbuhan as KoleksiTumbuhanModel
    from sqlalchemy import func
    
    # Build dynamic query based on group_by field
    group_column = getattr(KoleksiTumbuhanModel, group_by)
    
    result = await db.execute(
        select(group_column, func.count(KoleksiTumbuhanModel.id))
        .group_by(group_column)
    )
    
    rows = result.all()
    
    # Format results
    stats_groups = [
        KoleksiTumbuhanStatsGroup(
            group_value=str(row[0]) if row[0] is not None else "null",
            count=row[1]
        )
        for row in rows
    ]
    
    response = KoleksiTumbuhanStatsResponse(results=stats_groups)
    logger.info(f"Successfully returned stats grouped by '{group_by}' with {len(stats_groups)} groups")
    return response


@router.get("/map-clusters", response_model=dict)  # Return type depends on implementation
async def read_koleksi_map_clusters(
    taman_kehati_id: Optional[int] = None,
    zoom: int = 10, 
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get plant collection clustering for map visualization"""
    logger.info(f"Getting map clusters for taman {taman_kehati_id}, zoom: {zoom}, user: {current_user.email}")
    
    # This is a simplified implementation - in a real app, you would implement
    # proper clustering algorithm based on zoom level
    from app.models import KoleksiTumbuhan as KoleksiTumbuhanModel
    from sqlalchemy.future import select
    
    query = select(KoleksiTumbuhanModel).filter(
        KoleksiTumbuhanModel.latitude_taman.isnot(None),
        KoleksiTumbuhanModel.longitude_taman.isnot(None)
    )
    
    if taman_kehati_id:
        query = query.filter(KoleksiTumbuhanModel.taman_kehati_id == taman_kehati_id)
    
    result = await db.execute(query)
    collections = result.scalars().all()
    
    # Apply geo-masking for non-admin users
    if current_user.role not in ["super_admin", "admin_taman"]:
        for koleksi in collections:
            # Mask coordinates in the taman
            if koleksi.latitude_taman and koleksi.longitude_taman:
                koleksi.latitude_taman, koleksi.longitude_taman = mask_coordinates(
                    koleksi.latitude_taman, 
                    koleksi.longitude_taman, 
                    user_role=current_user.role,
                    species_type=koleksi.status_endemik
                )
    
    # For now, return a simple list of collections with coordinates
    clusters = []
    for col in collections:
        clusters.append({
            "id": col.id,
            "nama_ilmiah": col.nama_ilmiah,
            "latitude": float(col.latitude_taman) if col.latitude_taman else None,
            "longitude": float(col.longitude_taman) if col.longitude_taman else None,
            "status_endemik": col.status_endemik
        })
    
    logger.info(f"Successfully returned {len(clusters)} clusters for map visualization")
    return {"clusters": clusters, "zoom": zoom}


@router.post("/", response_model=KoleksiTumbuhanResponse)
async def create_koleksi_tumbuhan(
    koleksi: KoleksiTumbuhanCreate,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new plant collection (admin only)"""
    logger.info(f"Creating new plant collection by admin user: {current_user.email}")
    
    # Check if user has permission to create collection for this taman
    from app.auth.utils import check_taman_access
    has_access = await check_taman_access(db, current_user, koleksi.taman_kehati_id)
    if not has_access and current_user.role != "super_admin":
        logger.warning(f"Unauthorized attempt to create collection for taman {koleksi.taman_kehati_id} by user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create collection for this taman"
        )
    
    db_koleksi = await create_koleksi(db, koleksi)
    logger.info(f"Successfully created plant collection '{db_koleksi.nama_ilmiah}' with ID: {db_koleksi.id}")
    return KoleksiTumbuhanResponse.from_orm(db_koleksi)


@router.patch("/{koleksi_id}", response_model=KoleksiTumbuhanResponse)
async def update_koleksi_tumbuhan(
    koleksi_id: int,
    koleksi: KoleksiTumbuhanUpdate,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a plant collection (admin only)"""
    logger.info(f"Updating plant collection ID {koleksi_id} by admin user: {current_user.email}")
    
    db_koleksi = await update_koleksi_tumbuhan(db, koleksi_id, koleksi)
    if not db_koleksi:
        logger.warning(f"Plant collection with ID {koleksi_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant collection not found"
        )
    
    # Check if user has permission to update collection for this taman
    from app.auth.utils import check_taman_access
    has_access = await check_taman_access(db, current_user, db_koleksi.taman_kehati_id)
    if not has_access and current_user.role != "super_admin":
        logger.warning(f"Unauthorized attempt to update collection {koleksi_id} by user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this collection"
        )
    
    logger.info(f"Successfully updated plant collection '{db_koleksi.nama_ilmiah}' with ID: {db_koleksi.id}")
    return KoleksiTumbuhanResponse.from_orm(db_koleksi)


@router.delete("/{koleksi_id}")
async def delete_koleksi_tumbuhan(
    koleksi_id: int,
    current_user = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a plant collection (admin only)"""
    logger.info(f"Deleting plant collection ID {koleksi_id} by admin user: {current_user.email}")
    
    success = await delete_koleksi_tumbuhan(db, koleksi_id)
    if not success:
        logger.warning(f"Plant collection with ID {koleksi_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plant collection not found"
        )
    
    logger.info(f"Successfully deleted plant collection ID {koleksi_id}")
    return {"message": "Plant collection deleted successfully"}