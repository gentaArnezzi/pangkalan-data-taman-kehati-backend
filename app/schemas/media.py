from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID


class MediaTypeEnum(str, Enum):
    foto = "foto"
    video = "video"


class MediaCategoryEnum(str, Enum):
    taman_umum = "taman_umum"
    tumbuhan_keseluruhan = "tumbuhan_keseluruhan"
    daun = "daun"
    bunga = "bunga"
    buah = "buah"
    batang = "batang"
    akar = "akar"
    lainnya = "lainnya"


class MediaBase(BaseModel):
    taman_kehati_id: Optional[int] = None
    koleksi_tumbuhan_id: Optional[int] = None
    media_type: MediaTypeEnum
    media_category: MediaCategoryEnum
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    caption: Optional[str] = None
    is_main_image: bool = False


class MediaCreate(MediaBase):
    pass


class MediaUpdate(BaseModel):
    caption: Optional[str] = None
    is_main_image: Optional[bool] = None


class MediaResponse(BaseModel):
    id: int
    taman_kehati_id: Optional[int]
    koleksi_tumbuhan_id: Optional[int]
    media_type: MediaTypeEnum
    media_category: MediaCategoryEnum
    file_name: str
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    caption: Optional[str]
    is_main_image: bool
    uploaded_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True