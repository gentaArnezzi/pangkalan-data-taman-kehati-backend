from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from .users import StatusPublikasiEnum


class ArtikelBase(BaseModel):
    judul: str
    ringkasan: Optional[str] = None
    konten: str
    cover_image_id: Optional[int] = None
    taman_kehati_id: Optional[int] = None
    kategori: Optional[str] = None
    tags: Optional[List[str]] = None


class ArtikelCreate(ArtikelBase):
    status: Optional[StatusPublikasiEnum] = StatusPublikasiEnum.draft
    author_id: UUID


class ArtikelUpdate(BaseModel):
    judul: Optional[str] = None
    slug: Optional[str] = None
    ringkasan: Optional[str] = None
    konten: Optional[str] = None
    cover_image_id: Optional[int] = None
    taman_kehati_id: Optional[int] = None
    kategori: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[StatusPublikasiEnum] = None


class ArtikelPublish(BaseModel):
    status: StatusPublikasiEnum = StatusPublikasiEnum.published


class ArtikelSetCover(BaseModel):
    cover_image_id: int


class ArtikelResponse(BaseModel):
    id: int
    judul: str
    slug: str
    ringkasan: Optional[str]
    konten: str
    cover_image_id: Optional[int]
    taman_kehati_id: Optional[int]
    kategori: Optional[str]
    tags: Optional[List[str]]
    status: StatusPublikasiEnum
    published_at: Optional[datetime]
    author_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtikelWithAuthorResponse(ArtikelResponse):
    author: Optional[dict] = None
    taman: Optional[dict] = None
    cover_image: Optional[dict] = None


class ArtikelListResponse(BaseModel):
    id: int
    judul: str
    slug: str
    ringkasan: Optional[str]
    cover_image_id: Optional[int]
    taman_kehati_id: Optional[int]
    kategori: Optional[str]
    tags: Optional[List[str]]
    status: StatusPublikasiEnum
    published_at: Optional[datetime]
    author_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True