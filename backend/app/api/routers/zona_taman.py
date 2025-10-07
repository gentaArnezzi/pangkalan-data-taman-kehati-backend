from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.database import get_db
from app.schemas.zona_taman import (
    ZonaTamanCreate, 
    ZonaTamanUpdate, 
    ZonaTamanResponse,
    ZonaTamanGeoResponse
)
from app.auth.utils import get_current_active_user, get_current_admin
from app.utils.logging_config import get_logger
from sqlalchemy import text, select
from app.models import ZonaTaman as ZonaTamanModel, KoleksiTumbuhan, StatusPublikasiEnum
from app.geo.utils import validate_geojson_polygon, geometry_to_geojson
from geoalchemy2 import WKTElement
from shapely import wkt
import shapely

router = APIRouter()
logger = get_logger(__name__)

@router.get("/", response_model=List[ZonaTamanResponse])
async def read_zona(
    taman_kehati_id: Optional[int] = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of zones, optionally filtered by taman_kehati_id"""
    logger.info(f"Fetching zones - user: {current_user.email}, taman_kehati_id: {taman_kehati_id}")
    
    from sqlalchemy.future import select
    
    query = select(ZonaTamanModel)
    
    if taman_kehati_id:
        query = query.filter(ZonaTamanModel.taman_kehati_id == taman_kehati_id)
    
    result = await db.execute(query)
    zona_list = result.scalars().all()
    
    logger.info(f"Successfully returned {len(zona_list)} zones")
    return [ZonaTamanResponse.from_orm(z) for z in zona_list]


@router.get("/{zona_id}/geo", response_model=ZonaTamanGeoResponse)
async def read_zona_geo(
    zona_id: int,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get zone geometry as GeoJSON Feature"""
    logger.info(f"Fetching zone geometry with ID {zona_id} for user: {current_user.email}")
    
    result = await db.execute(
        select(ZonaTamanModel)
        .filter(ZonaTamanModel.id == zona_id)
    )
    zona = result.scalars().first()
    
    if not zona:
        logger.warning(f"Zone with ID {zona_id} not found for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    # Convert polygon to GeoJSON using ST_AsGeoJSON
    if zona.poligon:
        polygon_result = await db.execute(
            text("SELECT ST_AsGeoJSON(:poligon) as geom"),
            {"poligon": zona.poligon}
        )
        polygon_row = polygon_result.fetchone()
        if polygon_row:
            geometry = json.loads(polygon_row.geom)
            
            geo_response = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "id": zona.id,
                    "kode_zona": zona.kode_zona,
                    "nama_zona": zona.nama_zona,
                    "warna": zona.warna
                }
            }
            
            logger.info(f"Successfully returned geometry for zone: {zona.nama_zona}")
            return geo_response
    
    # If no polygon or conversion failed, return empty feature
    logger.warning(f"No geometry found for zone {zona_id}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Zone geometry not found"
    )


@router.get("/{zona_id}/koleksi", response_model=List[dict])  # Using dict temporarily
async def read_zona_koleksi(
    zona_id: int,
    status_filter: Optional[StatusPublikasiEnum] = None,
    page: int = 1,
    size: int = 20,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get collections in a specific zone, with optional status filtering"""
    logger.info(f"Fetching collections for zone {zona_id} - user: {current_user.email}, status_filter: {status_filter}")
    
    skip = (page - 1) * size
    
    query = select(KoleksiTumbuhan).filter(KoleksiTumbuhan.zona_id == zona_id)
    
    if status_filter:
        query = query.filter(KoleksiTumbuhan.status == status_filter)
    
    query = query.offset(skip).limit(size)
    
    result = await db.execute(query)
    koleksi_list = result.scalars().all()
    
    # Convert to response format (will need to import proper schema later)
    from app.schemas.koleksi_tumbuhan import KoleksiTumbuhanResponse
    koleksi_responses = [KoleksiTumbuhanResponse.from_orm(k) for k in koleksi_list]
    
    logger.info(f"Successfully returned {len(koleksi_responses)} collections for zone {zona_id}")
    return koleksi_responses


@router.post("/import", response_model=ZonaTamanResponse)
async def import_zona_geojson(
    taman_kehati_id: int,
    geojson_data: dict,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Import zone from GeoJSON (Polygon only), validate SRID/rings"""
    logger.info(f"Importing zone from GeoJSON by admin user: {current_user.email}, for taman: {taman_kehati_id}")
    
    # Check if user has permission to create zone for this taman
    from app.auth.utils import check_taman_access
    has_access = await check_taman_access(db, current_user, taman_kehati_id)
    if not has_access and current_user.role != "super_admin":
        logger.warning(f"Unauthorized attempt to import zone for taman {taman_kehati_id} by user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to import zone for this taman"
        )
    
    # Validate that we have a GeoJSON object
    if not geojson_data or "type" not in geojson_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GeoJSON: missing type property"
        )
    
    # Validate that it's a polygon
    geom_type = geojson_data.get("type")
    if geom_type == "Feature":
        # Extract geometry from feature
        geometry = geojson_data.get("geometry")
        if not geometry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GeoJSON Feature: missing geometry"
            )
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
    elif geom_type in ["Polygon", "MultiPolygon"]:
        coordinates = geojson_data.get("coordinates")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid geometry type: {geom_type}. Only Polygon or Feature with Polygon geometry is supported."
        )
    
    # Validate the polygon
    if not validate_geojson_polygon({"type": "Polygon", "coordinates": coordinates}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid polygon: must be properly formed with closed rings and valid coordinates"
        )
    
    # Convert GeoJSON coordinates to WKT polygon
    try:
        # Create Shapely geometry from coordinates
        if geom_type == "Polygon":
            shape = shapely.geometry.Polygon(coordinates[0], holes=coordinates[1:] if len(coordinates) > 1 else [])
        elif geom_type == "MultiPolygon":
            # For MultiPolygon, just take the first polygon for now
            first_polygon_coords = coordinates[0][0]
            shape = shapely.geometry.Polygon(first_polygon_coords)
        else:
            raise ValueError(f"Unsupported geometry type: {geom_type}")
            
        # Convert to WKT with SRID 4326
        wkt_geom = shape.wkt
        wkb_geom = WKTElement(wkt_geom, srid=4326)
    except Exception as e:
        logger.error(f"Error converting GeoJSON to WKT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing GeoJSON geometry: {str(e)}"
        )
    
    # Create a new zone with the imported geometry
    from app.models import ZonaTaman as ZonaTamanModel
    
    # Generate a default name if not provided in properties
    name = geojson_data.get("properties", {}).get("name", f"Zone_{taman_kehati_id}_{len(str(coordinates))}")
    code = geojson_data.get("properties", {}).get("kode_zona", f"ZONE_{taman_kehati_id}_{len(str(coordinates))}")
    
    db_zona = ZonaTamanModel(
        taman_kehati_id=taman_kehati_id,
        kode_zona=code,
        nama_zona=name,
        deskripsi=geojson_data.get("properties", {}).get("description", ""),
        poligon=wkb_geom
    )
    
    db.add(db_zona)
    await db.commit()
    await db.refresh(db_zona)
    
    logger.info(f"Successfully imported zone '{db_zona.nama_zona}' with ID: {db_zona.id} from GeoJSON")
    return ZonaTamanResponse.from_orm(db_zona)


@router.post("/", response_model=ZonaTamanResponse)
async def create_zona(
    zona: ZonaTamanCreate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new zone (admin only)"""
    logger.info(f"Creating new zone by admin user: {current_user.email}")
    
    # Check if user has permission to create zone for this taman
    from app.auth.utils import check_taman_access
    has_access = await check_taman_access(db, current_user, zona.taman_kehati_id)
    if not has_access and current_user.role != "super_admin":
        logger.warning(f"Unauthorized attempt to create zone for taman {zona.taman_kehati_id} by user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create zone for this taman"
        )
    
    from app.models import ZonaTaman as ZonaTamanModel
    db_zona = ZonaTamanModel(**zona.dict())
    db.add(db_zona)
    await db.commit()
    await db.refresh(db_zona)
    
    logger.info(f"Successfully created zone '{db_zona.nama_zona}' with ID: {db_zona.id}")
    return ZonaTamanResponse.from_orm(db_zona)


@router.patch("/{zona_id}", response_model=ZonaTamanResponse)
async def update_zona(
    zona_id: int,
    zona_update: ZonaTamanUpdate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update a zone (admin only)"""
    logger.info(f"Updating zone ID {zona_id} by admin user: {current_user.email}")
    
    result = await db.execute(
        select(ZonaTamanModel)
        .filter(ZonaTamanModel.id == zona_id)
    )
    db_zona = result.scalars().first()
    
    if not db_zona:
        logger.warning(f"Zone with ID {zona_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    # Check if user has permission to update zone for this taman
    from app.auth.utils import check_taman_access
    has_access = await check_taman_access(db, current_user, db_zona.taman_kehati_id)
    if not has_access and current_user.role != "super_admin":
        logger.warning(f"Unauthorized attempt to update zone {zona_id} by user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this zone"
        )
    
    update_data = zona_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zona, field, value)
    
    await db.commit()
    await db.refresh(db_zona)
    
    logger.info(f"Successfully updated zone '{db_zona.nama_zona}' with ID: {db_zona.id}")
    return ZonaTamanResponse.from_orm(db_zona)


@router.delete("/{zona_id}")
async def delete_zona(
    zona_id: int,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a zone (admin only) - with FK safety checks"""
    logger.info(f"Deleting zone ID {zona_id} by admin user: {current_user.email}")
    
    result = await db.execute(
        select(ZonaTamanModel)
        .filter(ZonaTamanModel.id == zona_id)
    )
    db_zona = result.scalars().first()
    
    if not db_zona:
        logger.warning(f"Zone with ID {zona_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Zone not found"
        )
    
    # Check if user has permission to delete zone for this taman
    from app.auth.utils import check_taman_access
    has_access = await check_taman_access(db, current_user, db_zona.taman_kehati_id)
    if not has_access and current_user.role != "super_admin":
        logger.warning(f"Unauthorized attempt to delete zone {zona_id} by user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this zone"
        )
    
    # Check for collections in this zone (FK safety check)  
    result = await db.execute(
        select(KoleksiTumbuhan)
        .filter(KoleksiTumbuhan.zona_id == zona_id)
    )
    collections_in_zone = result.scalars().all()
    
    if collections_in_zone:
        logger.warning(f"Cannot delete zone {zona_id} - it has {len(collections_in_zone)} associated collections")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete zone {zona_id} - it has {len(collections_in_zone)} associated collections"
        )
    
    await db.delete(db_zona)
    await db.commit()
    
    logger.info(f"Successfully deleted zone ID {zona_id}")
    return {"message": "Zone deleted successfully"}