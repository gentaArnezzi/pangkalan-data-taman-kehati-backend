from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from fastapi.responses import JSONResponse

from app.database import get_db
from app.schemas.artikel import (
    ArtikelCreate,
    ArtikelUpdate,
    ArtikelPublish,
    ArtikelSetCover,
    ArtikelResponse,
    ArtikelWithAuthorResponse,
    ArtikelListResponse
)
from app.auth.utils import get_current_active_user, get_current_admin, get_current_super_admin
from app.crud.artikel import (
    get_artikel,
    get_artikel_by_slug,
    get_artikels,
    create_artikel as create_artikel_db,
    update_artikel,
    delete_artikel,
    publish_artikel,
    set_artikel_cover
)
from app.utils.logging_config import get_logger
from app.models import StatusPublikasiEnum
from app.utils.etag import generate_etag, validate_if_match

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=List[ArtikelListResponse],
            summary="Get list of articles",
            description="Get list of articles with pagination, filtering, and search capabilities. "
                        "Non-admin users only see published articles.",
            responses={
                200: {
                    "description": "List of articles",
                    "content": {
                        "application/json": {
                            "example": {
                                "id": 1,
                                "judul": "Keunikan Flora di Taman Kehati",
                                "slug": "keunikan-flora-di-taman-kehati",
                                "ringkasan": "Artikel tentang keunikan flora yang terdapat di Taman Keanekaragaman Hayati...",
                                "cover_image_id": 5,
                                "taman_kehati_id": 1,
                                "kategori": "Flora",
                                "tags": ["flora", "taman-kehati", "konservasi"],
                                "status": "published",
                                "published_at": "2023-06-15T10:30:00",
                                "author_id": "123e4567-e89b-12d3-a456-426614174000",
                                "created_at": "2023-06-10T08:00:00",
                                "updated_at": "2023-06-15T10:30:00"
                            }
                        }
                    }
                }
            })
async def read_artikels(
    page: int = 1,
    size: int = 20,
    sort: Optional[str] = "published_at",
    q: Optional[str] = None,
    status: Optional[StatusPublikasiEnum] = None,
    taman_kehati_id: Optional[int] = None,
    kategori: Optional[str] = None,
    author_id: Optional[UUID] = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of articles with pagination, filtering, and search"""
    skip = (page - 1) * size
    limit = size

    logger.info(f"Fetching Artikel list - user: {current_user.email}, page: {page}, size: {size}, "
                f"status: {status}, taman_kehati_id: {taman_kehati_id}, q: {q}")

    # For non-admin users, only show published articles
    if current_user.role not in ["super_admin", "admin_taman"]:
        if status and status != StatusPublikasiEnum.published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non-admin users can only access published articles"
            )
        if not status:
            status = StatusPublikasiEnum.published

    artikels = await get_artikels(
        db, 
        skip=skip, 
        limit=limit,
        status=status.value if status else None,
        taman_kehati_id=taman_kehati_id,
        kategori=kategori,
        author_id=author_id,
        q=q
    )

    logger.info(f"Successfully returned {len(artikels)} Artikel records")
    return artikels


@router.get("/{artikel_id}", response_model=ArtikelWithAuthorResponse)
async def read_artikel(
    artikel_id: int,
    response: Response,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific article by ID"""
    logger.info(f"Fetching Artikel with ID {artikel_id} for user: {current_user.email}")
    artikel = await get_artikel(db, artikel_id)
    if not artikel:
        logger.warning(f"Artikel with ID {artikel_id} not found for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )

    # For non-admin users, only allow access to published articles
    if current_user.role not in ["super_admin", "admin_taman"]:
        if artikel.status != StatusPublikasiEnum.published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: article is not published"
            )

    # Generate and set ETag
    etag = generate_etag(artikel)
    response.headers["ETag"] = etag
    
    logger.info(f"Successfully returned Artikel: {artikel.judul}")
    return artikel


@router.get("/slug/{slug}", response_model=ArtikelWithAuthorResponse)
async def read_artikel_by_slug(
    slug: str,
    response: Response,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific article by slug"""
    logger.info(f"Fetching Artikel with slug {slug} for user: {current_user.email}")
    artikel = await get_artikel_by_slug(db, slug)
    if not artikel:
        logger.warning(f"Artikel with slug {slug} not found for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )

    # For non-admin users, only allow access to published articles
    if current_user.role not in ["super_admin", "admin_taman"]:
        if artikel.status != StatusPublikasiEnum.published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: article is not published"
            )

    # Generate and set ETag
    etag = generate_etag(artikel)
    response.headers["ETag"] = etag
    
    logger.info(f"Successfully returned Artikel: {artikel.judul}")
    return artikel


@router.get("/{artikel_id}/related", response_model=List[ArtikelListResponse])
async def read_artikel_related(
    artikel_id: int,
    limit: int = 5,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get related articles for a specific article"""
    logger.info(f"Fetching related articles for Artikel ID {artikel_id}, limit: {limit}, user: {current_user.email}")
    
    # Get the current article to use for finding related ones
    current_artikel = await get_artikel(db, artikel_id)
    if not current_artikel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )
    
    # For non-admin users, only allow access to published articles
    if current_user.role not in ["super_admin", "admin_taman"]:
        if current_artikel.status != StatusPublikasiEnum.published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: article is not published"
            )
    
    # Find related articles: same taman, same author, or same category
    related_artikels = []
    
    # Build query to find related articles
    from sqlalchemy import or_, func
    from app.models import Artikel as ArtikelModel
    from sqlalchemy.future import select

    query = select(ArtikelModel).filter(
        ArtikelModel.id != artikel_id,  # Exclude current article
        ArtikelModel.status == StatusPublikasiEnum.published  # Only published articles
    )
    
    # Add filters for related content
    conditions = []
    if current_artikel.taman_kehati_id:
        conditions.append(ArtikelModel.taman_kehati_id == current_artikel.taman_kehati_id)
    if current_artikel.author_id:
        conditions.append(ArtikelModel.author_id == current_artikel.author_id)
    if current_artikel.kategori:
        conditions.append(ArtikelModel.kategori == current_artikel.kategori)
    
    if conditions:
        query = query.filter(or_(*conditions))
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    related_artikels = result.scalars().all()
    
    logger.info(f"Successfully returned {len(related_artikels)} related articles for Artikel ID {artikel_id}")
    return related_artikels


async def create_artikel(
    artikel: ArtikelCreate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new article"""
    logger.info(f"Creating new Artikel by admin user: {current_user.email}")
    
    # If user is not super_admin, ensure they can only create articles for their assigned taman
    if current_user.role == "admin_taman" and artikel.taman_kehati_id:
        if current_user.taman_kehati_id != artikel.taman_kehati_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin taman can only create articles for their assigned taman"
            )
    
    # Set author to current user if not specified
    if not artikel.author_id:
        artikel.author_id = current_user.id
    
    db_artikel = await create_artikel_db(
        db, 
        artikel, 
        current_user_id=current_user.id
    )
    logger.info(f"Successfully created Artikel '{db_artikel.judul}' with ID: {db_artikel.id}")
    return db_artikel


@router.put("/{artikel_id}", response_model=ArtikelResponse)
async def update_artikel_endpoint(
    artikel_id: int,
    artikel: ArtikelUpdate,
    response: Response,
    if_match: str = None,  # If-Match header for optimistic concurrency
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an article"""
    logger.info(f"Updating Artikel ID {artikel_id} by admin user: {current_user.email}")
    
    # Check if article exists and get it
    existing_artikel = await get_artikel(db, artikel_id)
    if not existing_artikel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )
    
    # Check permissions - admin_taman can only edit articles in their taman
    if current_user.role == "admin_taman":
        if existing_artikel.taman_kehati_id and current_user.taman_kehati_id != existing_artikel.taman_kehati_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin taman can only update articles for their assigned taman"
            )
    
    # Check If-Match header for optimistic concurrency
    if if_match:
        current_etag = generate_etag(existing_artikel)
        if not validate_if_match(if_match, current_etag):
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="Resource has been modified by another client. Please refresh and try again."
            )
    
    db_artikel = await update_artikel(
        db, 
        artikel_id, 
        artikel, 
        current_user_id=current_user.id
    )
    if not db_artikel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )
        
    # Generate and set new ETag after update
    new_etag = generate_etag(db_artikel)
    response.headers["ETag"] = new_etag
    
    logger.info(f"Successfully updated Artikel '{db_artikel.judul}' with ID: {db_artikel.id}")
    return db_artikel


@router.patch("/{artikel_id}/publish", response_model=ArtikelResponse)
async def publish_artikel_endpoint(
    artikel_id: int,
    publish_data: ArtikelPublish,
    response: Response,
    if_match: str = None,  # If-Match header for optimistic concurrency
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Publish an article (sets status and published_at)"""
    logger.info(f"Publishing Artikel ID {artikel_id} by admin user: {current_user.email}")
    
    # Check if article exists and get it
    existing_artikel = await get_artikel(db, artikel_id)
    if not existing_artikel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )
    
    # Check permissions - admin_taman can only publish articles in their taman
    if current_user.role == "admin_taman":
        if existing_artikel.taman_kehati_id and current_user.taman_kehati_id != existing_artikel.taman_kehati_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin taman can only publish articles for their assigned taman"
            )
    
    # Check If-Match header for optimistic concurrency
    if if_match:
        current_etag = generate_etag(existing_artikel)
        if not validate_if_match(if_match, current_etag):
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="Resource has been modified by another client. Please refresh and try again."
            )
    
    db_artikel = await publish_artikel(
        db, 
        artikel_id, 
        current_user_id=current_user.id
    )
    if not db_artikel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )
        
    # Generate and set new ETag after update
    new_etag = generate_etag(db_artikel)
    response.headers["ETag"] = new_etag
    
    logger.info(f"Successfully published Artikel '{db_artikel.judul}' with ID: {db_artikel.id}")
    return db_artikel


@router.patch("/{artikel_id}/cover", response_model=ArtikelResponse)
async def set_artikel_cover_endpoint(
    artikel_id: int,
    cover_data: ArtikelSetCover,
    response: Response,
    if_match: str = None,  # If-Match header for optimistic concurrency
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Set cover image for an article"""
    logger.info(f"Setting cover image for Artikel ID {artikel_id} by admin user: {current_user.email}")
    
    # Check if article exists and get it
    existing_artikel = await get_artikel(db, artikel_id)
    if not existing_artikel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )
    
    # Check permissions - admin_taman can only update articles in their taman
    if current_user.role == "admin_taman":
        if existing_artikel.taman_kehati_id and current_user.taman_kehati_id != existing_artikel.taman_kehati_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin taman can only update articles for their assigned taman"
            )
    
    # Check If-Match header for optimistic concurrency
    if if_match:
        current_etag = generate_etag(existing_artikel)
        if not validate_if_match(if_match, current_etag):
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="Resource has been modified by another client. Please refresh and try again."
            )
    
    db_artikel = await set_artikel_cover(
        db, 
        artikel_id, 
        cover_data.cover_image_id,
        current_user_id=current_user.id
    )
    if not db_artikel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )
        
    # Generate and set new ETag after update
    new_etag = generate_etag(db_artikel)
    response.headers["ETag"] = new_etag
    
    logger.info(f"Successfully updated cover for Artikel '{db_artikel.judul}' with ID: {db_artikel.id}")
    return db_artikel


@router.delete("/{artikel_id}")
async def delete_artikel_endpoint(
    artikel_id: int,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete an article"""
    logger.info(f"Deleting Artikel ID {artikel_id} by admin user: {current_user.email}")
    
    # Check if article exists and get it
    existing_artikel = await get_artikel(db, artikel_id)
    if not existing_artikel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )
    
    # Check permissions - admin_taman can only delete articles in their taman
    if current_user.role == "admin_taman":
        if existing_artikel.taman_kehati_id and current_user.taman_kehati_id != existing_artikel.taman_kehati_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin taman can only delete articles for their assigned taman"
            )
    
    success = await delete_artikel(db, artikel_id, current_user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artikel not found"
        )
    logger.info(f"Successfully deleted Artikel ID {artikel_id}")
    return {"message": "Artikel deleted successfully"}