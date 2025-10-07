from fastapi import APIRouter, Depends
from app.auth.utils import get_current_active_user
from app.utils.logging_config import get_logger
from app.schemas.meta import MetaEnumsResponse
from app.models import (
    StatusPublikasiEnum,
    StatusEndemikEnum,
    MediaTypeEnum,
    MediaCategoryEnum,
    TipeTamanEnum,
    UserRoleEnum
)

router = APIRouter()
logger = get_logger(__name__)

@router.get("/enums", response_model=MetaEnumsResponse)
async def get_meta_enums(current_user=Depends(get_current_active_user)):
    """Get all enum values for frontend use"""
    logger.info(f"Fetching enum values for user: {current_user.email}")
    
    response = MetaEnumsResponse(
        status_publikasi=[e.value for e in StatusPublikasiEnum],
        status_endemik=[e.value for e in StatusEndemikEnum],
        media_type=[e.value for e in MediaTypeEnum],
        media_category=[e.value for e in MediaCategoryEnum],
        tipe_taman=[e.value for e in TipeTamanEnum],
        user_role=[e.value for e in UserRoleEnum]
    )
    
    logger.info("Successfully returned enum values")
    return response