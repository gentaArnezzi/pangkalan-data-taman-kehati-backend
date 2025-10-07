from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_, or_
from uuid import UUID
from typing import List, Optional
from slugify import slugify

from app.models import Artikel as ArtikelModel, Media, TamanKehati, User as UserModel
from app.schemas.artikel import ArtikelCreate, ArtikelUpdate, ArtikelResponse
from app.utils.logging_config import get_logger
from app.audit.utils import log_audit_entry

logger = get_logger(__name__)


async def get_artikel(db: AsyncSession, artikel_id: int) -> Optional[ArtikelModel]:
    """Get an article by ID"""
    logger.info(f"Fetching Artikel with ID: {artikel_id}")
    result = await db.execute(
        select(ArtikelModel)
        .options(
            selectinload(ArtikelModel.coverImage),
            selectinload(ArtikelModel.taman),
            selectinload(ArtikelModel.author)
        )
        .filter(ArtikelModel.id == artikel_id)
    )
    artikel = result.scalars().first()
    if artikel:
        logger.debug(f"Successfully retrieved Artikel: {artikel.judul}")
    else:
        logger.warning(f"Artikel not found with ID: {artikel_id}")
    return artikel


async def get_artikel_by_slug(db: AsyncSession, slug: str) -> Optional[ArtikelModel]:
    """Get an article by slug"""
    logger.info(f"Fetching Artikel with slug: {slug}")
    result = await db.execute(
        select(ArtikelModel)
        .options(
            selectinload(ArtikelModel.coverImage),
            selectinload(ArtikelModel.taman),
            selectinload(ArtikelModel.author)
        )
        .filter(ArtikelModel.slug == slug)
    )
    artikel = result.scalars().first()
    if artikel:
        logger.debug(f"Successfully retrieved Artikel: {artikel.judul}")
    else:
        logger.warning(f"Artikel not found with slug: {slug}")
    return artikel


async def get_artikels(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    taman_kehati_id: Optional[int] = None,
    kategori: Optional[str] = None,
    author_id: Optional[UUID] = None,
    q: Optional[str] = None
) -> List[ArtikelModel]:
    """Get a list of articles with optional filters"""
    logger.info(f"Fetching Artikel list with skip={skip}, limit={limit}, status={status}, taman_kehati_id={taman_kehati_id}")

    query = select(ArtikelModel).options(
        selectinload(ArtikelModel.coverImage),
        selectinload(ArtikelModel.taman),
        selectinload(ArtikelModel.author)
    ).offset(skip).limit(limit)

    # Build filters
    filters = []

    if status:
        filters.append(ArtikelModel.status == status)
    
    if taman_kehati_id:
        filters.append(ArtikelModel.taman_kehati_id == taman_kehati_id)
        
    if kategori:
        filters.append(ArtikelModel.kategori == kategori)
        
    if author_id:
        filters.append(ArtikelModel.author_id == author_id)
        
    if q:
        filters.append(
            or_(
                ArtikelModel.judul.ilike(f"%{q}%"),
                ArtikelModel.ringkasan.ilike(f"%{q}%"),
                ArtikelModel.konten.ilike(f"%{q}%")
            )
        )

    if filters:
        query = query.filter(and_(*filters))

    # Apply ordering by published_at (descending) if published, otherwise by created_at
    query = query.order_by(
        func.coalesce(ArtikelModel.published_at, ArtikelModel.created_at).desc()
    )

    result = await db.execute(query)
    artikels = result.scalars().all()
    logger.debug(f"Retrieved {len(artikels)} Artikel records")
    return artikels


async def create_artikel(
    db: AsyncSession,
    artikel: ArtikelCreate,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> ArtikelModel:
    """Create a new article"""
    logger.info(f"Creating new Artikel: {artikel.judul}")

    # Generate slug from title
    slug = slugify(artikel.judul)
    
    # Ensure unique slug
    original_slug = slug
    counter = 1
    while True:
        result = await db.execute(
            select(ArtikelModel).filter(ArtikelModel.slug == slug)
        )
        if result.scalars().first() is None:
            break
        slug = f"{original_slug}-{counter}"
        counter += 1

    db_artikel = ArtikelModel(
        judul=artikel.judul,
        slug=slug,
        ringkasan=artikel.ringkasan,
        konten=artikel.konten,
        cover_image_id=artikel.cover_image_id,
        taman_kehati_id=artikel.taman_kehati_id,
        kategori=artikel.kategori,
        tags=artikel.tags,
        status=artikel.status,
        author_id=artikel.author_id
    )

    db.add(db_artikel)
    await db.flush()  # Use flush to get the ID before committing

    # Log audit entry
    await log_audit_entry(
        db,
        user_id=current_user_id,
        action="CREATE",
        table_name="artikel",
        record_id=db_artikel.id,
        new_data=artikel.dict(),
        ip_address=ip_address,
        user_agent=user_agent
    )

    await db.commit()
    await db.refresh(db_artikel)
    logger.info(f"Successfully created Artikel with ID: {db_artikel.id}")
    return db_artikel


async def update_artikel(
    db: AsyncSession,
    artikel_id: int,
    artikel: ArtikelUpdate,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[ArtikelModel]:
    """Update an article"""
    logger.info(f"Updating Artikel with ID: {artikel_id}")
    result = await db.execute(
        select(ArtikelModel).filter(ArtikelModel.id == artikel_id)
    )
    db_artikel = result.scalars().first()

    if not db_artikel:
        logger.warning(f"Artikel not found for update with ID: {artikel_id}")
        return None

    # Capture old data for audit
    old_data = {
        "id": db_artikel.id,
        "judul": db_artikel.judul,
        "slug": db_artikel.slug,
        "ringkasan": db_artikel.ringkasan,
        "konten": db_artikel.konten,
        "cover_image_id": db_artikel.cover_image_id,
        "taman_kehati_id": db_artikel.taman_kehati_id,
        "kategori": db_artikel.kategori,
        "tags": db_artikel.tags,
        "status": db_artikel.status.value if hasattr(db_artikel.status, 'value') else str(db_artikel.status),
        "published_at": str(db_artikel.published_at) if db_artikel.published_at else None,
        "author_id": str(db_artikel.author_id),
        "created_at": str(db_artikel.created_at),
        "updated_at": str(db_artikel.updated_at)
    }

    update_data = artikel.dict(exclude_unset=True)
    logger.debug(f"Updating Artikel {artikel_id} with data: {update_data}")

    # Handle slug update - if title changes, regenerate slug
    if 'judul' in update_data and update_data['judul'] != db_artikel.judul:
        slug = slugify(update_data['judul'])
        # Ensure unique slug
        original_slug = slug
        counter = 1
        while True:
            result = await db.execute(
                select(ArtikelModel).filter(
                    ArtikelModel.slug == slug,
                    ArtikelModel.id != artikel_id  # Exclude current article from check
                )
            )
            if result.scalars().first() is None:
                break
            slug = f"{original_slug}-{counter}"
            counter += 1
        update_data['slug'] = slug

    for field, value in update_data.items():
        setattr(db_artikel, field, value)

    await db.commit()
    await db.refresh(db_artikel)

    # Log audit entry
    await log_audit_entry(
        db,
        user_id=current_user_id,
        action="UPDATE",
        table_name="artikel",
        record_id=db_artikel.id,
        old_data=old_data,
        new_data={**old_data, **update_data},
        ip_address=ip_address,
        user_agent=user_agent
    )

    logger.info(f"Successfully updated Artikel with ID: {artikel_id}")
    return db_artikel


async def delete_artikel(
    db: AsyncSession,
    artikel_id: int,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> bool:
    """Delete an article"""
    logger.info(f"Deleting Artikel with ID: {artikel_id}")
    result = await db.execute(
        select(ArtikelModel).filter(ArtikelModel.id == artikel_id)
    )
    db_artikel = result.scalars().first()

    if not db_artikel:
        logger.warning(f"Artikel not found for deletion with ID: {artikel_id}")
        return False

    # Capture old data for audit
    old_data = {
        "id": db_artikel.id,
        "judul": db_artikel.judul,
        "slug": db_artikel.slug,
        "ringkasan": db_artikel.ringkasan,
        "konten": db_artikel.konten,
        "cover_image_id": db_artikel.cover_image_id,
        "taman_kehati_id": db_artikel.taman_kehati_id,
        "kategori": db_artikel.kategori,
        "tags": db_artikel.tags,
        "status": db_artikel.status.value if hasattr(db_artikel.status, 'value') else str(db_artikel.status),
        "published_at": str(db_artikel.published_at) if db_artikel.published_at else None,
        "author_id": str(db_artikel.author_id),
        "created_at": str(db_artikel.created_at),
        "updated_at": str(db_artikel.updated_at)
    }

    await db.delete(db_artikel)
    await db.flush()  # Use flush to delete before logging

    # Log audit entry
    await log_audit_entry(
        db,
        user_id=current_user_id,
        action="DELETE",
        table_name="artikel",
        record_id=db_artikel.id,
        old_data=old_data,
        ip_address=ip_address,
        user_agent=user_agent
    )

    await db.commit()
    logger.info(f"Successfully deleted Artikel with ID: {artikel_id}")
    return True


async def publish_artikel(
    db: AsyncSession,
    artikel_id: int,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[ArtikelModel]:
    """Publish an article (set status to published and set published_at)"""
    logger.info(f"Publishing Artikel with ID: {artikel_id}")
    result = await db.execute(
        select(ArtikelModel).filter(ArtikelModel.id == artikel_id)
    )
    db_artikel = result.scalars().first()

    if not db_artikel:
        logger.warning(f"Artikel not found for publishing with ID: {artikel_id}")
        return None

    # Capture old data for audit
    old_data = {
        "id": db_artikel.id,
        "judul": db_artikel.judul,
        "slug": db_artikel.slug,
        "ringkasan": db_artikel.ringkasan,
        "konten": db_artikel.konten,
        "cover_image_id": db_artikel.cover_image_id,
        "taman_kehati_id": db_artikel.taman_kehati_id,
        "kategori": db_artikel.kategori,
        "tags": db_artikel.tags,
        "status": db_artikel.status.value if hasattr(db_artikel.status, 'value') else str(db_artikel.status),
        "published_at": str(db_artikel.published_at) if db_artikel.published_at else None,
        "author_id": str(db_artikel.author_id),
        "created_at": str(db_artikel.created_at),
        "updated_at": str(db_artikel.updated_at)
    }

    # Update status and published_at
    db_artikel.status = "published"
    if not db_artikel.published_at:
        from datetime import datetime
        db_artikel.published_at = datetime.utcnow()

    await db.commit()
    await db.refresh(db_artikel)

    # Log audit entry
    await log_audit_entry(
        db,
        user_id=current_user_id,
        action="UPDATE",
        table_name="artikel",
        record_id=db_artikel.id,
        old_data=old_data,
        new_data={
            **old_data,
            "status": "published",
            "published_at": str(db_artikel.published_at)
        },
        ip_address=ip_address,
        user_agent=user_agent
    )

    logger.info(f"Successfully published Artikel with ID: {artikel_id}")
    return db_artikel


async def set_artikel_cover(
    db: AsyncSession,
    artikel_id: int,
    cover_image_id: int,
    current_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Optional[ArtikelModel]:
    """Set cover image for an article"""
    logger.info(f"Setting cover image {cover_image_id} for Artikel with ID: {artikel_id}")
    result = await db.execute(
        select(ArtikelModel).filter(ArtikelModel.id == artikel_id)
    )
    db_artikel = result.scalars().first()

    if not db_artikel:
        logger.warning(f"Artikel not found for cover update with ID: {artikel_id}")
        return None

    # Capture old data for audit
    old_data = {
        "id": db_artikel.id,
        "judul": db_artikel.judul,
        "cover_image_id": db_artikel.cover_image_id,
        "updated_at": str(db_artikel.updated_at)
    }

    # Update cover image
    db_artikel.cover_image_id = cover_image_id

    await db.commit()
    await db.refresh(db_artikel)

    # Log audit entry
    await log_audit_entry(
        db,
        user_id=current_user_id,
        action="UPDATE",
        table_name="artikel",
        record_id=db_artikel.id,
        old_data=old_data,
        new_data={
            **old_data,
            "cover_image_id": cover_image_id
        },
        ip_address=ip_address,
        user_agent=user_agent
    )

    logger.info(f"Successfully updated cover image for Artikel with ID: {artikel_id}")
    return db_artikel