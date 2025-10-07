from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import os
from pathlib import Path

from app.database import get_db
from app.schemas.media import MediaCreate, MediaUpdate, MediaResponse, MediaTypeEnum, MediaCategoryEnum
from app.auth.utils import get_current_active_user, get_current_admin
from app.utils.logging_config import get_logger
from sqlalchemy import select
from app.models import Media as MediaModel, TamanKehati, KoleksiTumbuhan, User as UserModel
import uuid
from datetime import datetime

router = APIRouter()
logger = get_logger(__name__)

@router.post("/", response_model=MediaResponse)
async def upload_media(
    file: UploadFile = File(...),
    media_type: MediaTypeEnum = MediaTypeEnum.foto,
    media_category: MediaCategoryEnum = MediaCategoryEnum.taman_umum,
    koleksi_tumbuhan_id: Optional[int] = None,
    taman_kehati_id: Optional[int] = None,
    caption: Optional[str] = None,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload media file (multipart) with metadata"""
    logger.info(f"Uploading media file '{file.filename}' by user: {current_user.email}")
    
    # Validate that either taman or koleksi ID is provided
    if not taman_kehati_id and not koleksi_tumbuhan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either taman_kehati_id or koleksi_tumbuhan_id must be provided"
        )
    
    # Validate taman access if provided
    if taman_kehati_id:
        from app.auth.utils import check_taman_access
        has_access = await check_taman_access(db, current_user, taman_kehati_id)
        if not has_access and current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload media for this taman"
            )
    
    # Validate koleksi access if provided
    if koleksi_tumbuhan_id:
        from app.models import KoleksiTumbuhan
        result = await db.execute(
            select(KoleksiTumbuhan).filter(KoleksiTumbuhan.id == koleksi_tumbuhan_id)
        )
        koleksi = result.scalars().first()
        if not koleksi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Koleksi not found"
            )
        
        from app.auth.utils import check_taman_access
        has_access = await check_taman_access(db, current_user, koleksi.taman_kehati_id)
        if not has_access and current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload media for this koleksi"
            )
    
    # Validate file type
    allowed_types = {
        MediaTypeEnum.foto: ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"],
        MediaTypeEnum.video: ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska"]
    }
    
    if file.content_type not in allowed_types[media_type]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type for {media_type.value}: {file.content_type}"
        )
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create directory path (you might want to configure this in settings)
    upload_dir = Path("uploads/media")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)
    
    # Create media record
    media_data = MediaCreate(
        taman_kehati_id=taman_kehati_id,
        koleksi_tumbuhan_id=koleksi_tumbuhan_id,
        media_type=media_type,
        media_category=media_category,
        file_name=file.filename,
        file_path=str(file_path),
        file_size=file.size if hasattr(file, 'size') else len(await file.read()),
        mime_type=file.content_type,
        caption=caption,
        is_main_image=False
    )
    
    db_media = MediaModel(
        **media_data.dict(),
        uploaded_by=current_user.id
    )
    
    db.add(db_media)
    await db.commit()
    await db.refresh(db_media)
    
    logger.info(f"Successfully uploaded media '{file.filename}' with ID: {db_media.id}")
    return MediaResponse.from_orm(db_media)


@router.get("/", response_model=List[MediaResponse])
async def read_media(
    koleksi_tumbuhan_id: Optional[int] = None,
    taman_kehati_id: Optional[int] = None,
    is_main_image: Optional[bool] = None,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of media with optional filtering"""
    logger.info(f"Fetching media - user: {current_user.email}, filters: koleksi_tumbuhan_id={koleksi_tumbuhan_id}, taman_kehati_id={taman_kehati_id}, is_main_image={is_main_image}")
    
    query = select(MediaModel)
    
    filters = []
    if koleksi_tumbuhan_id:
        filters.append(MediaModel.koleksi_tumbuhan_id == koleksi_tumbuhan_id)
    
    if taman_kehati_id:
        filters.append(MediaModel.taman_kehati_id == taman_kehati_id)
        
    if is_main_image is not None:
        filters.append(MediaModel.is_main_image == is_main_image)
    
    if filters:
        from sqlalchemy import and_
        query = query.filter(and_(*filters))
    
    result = await db.execute(query)
    media_list = result.scalars().all()
    
    logger.info(f"Successfully returned {len(media_list)} media items")
    return [MediaResponse.from_orm(m) for m in media_list]


@router.patch("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: int,
    media_update: MediaUpdate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update media metadata (caption, is_main_image)"""
    logger.info(f"Updating media ID {media_id} by admin user: {current_user.email}")
    
    result = await db.execute(
        select(MediaModel).filter(MediaModel.id == media_id)
    )
    db_media = result.scalars().first()
    
    if not db_media:
        logger.warning(f"Media with ID {media_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    # Update fields
    update_data = media_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_media, field, value)
    
    await db.commit()
    await db.refresh(db_media)
    
    logger.info(f"Successfully updated media ID {media_id}")
    return MediaResponse.from_orm(db_media)


@router.delete("/{media_id}")
async def delete_media(
    media_id: int,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete media file and record"""
    logger.info(f"Deleting media ID {media_id} by admin user: {current_user.email}")
    
    result = await db.execute(
        select(MediaModel).filter(MediaModel.id == media_id)
    )
    db_media = result.scalars().first()
    
    if not db_media:
        logger.warning(f"Media with ID {media_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    # Delete the actual file
    try:
        if os.path.exists(db_media.file_path):
            os.remove(db_media.file_path)
    except Exception as e:
        logger.error(f"Failed to delete media file {db_media.file_path}: {str(e)}")
        # Still proceed with DB deletion even if file deletion fails
    
    await db.delete(db_media)
    await db.commit()
    
    logger.info(f"Successfully deleted media ID {media_id}")
    return {"message": "Media deleted successfully"}