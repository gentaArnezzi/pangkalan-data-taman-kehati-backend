from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import UUID


class UserRoleEnum(str, Enum):
    super_admin = "super_admin"
    admin_taman = "admin_taman"
    viewer = "viewer"


class StatusPublikasiEnum(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class BaseUser(BaseModel):
    email: EmailStr
    nama: str
    role: UserRoleEnum = UserRoleEnum.viewer
    is_active: bool = True
    taman_kehati_id: Optional[int] = None


class UserCreate(BaseUser):
    password: str


class UserUpdate(BaseModel):
    nama: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None
    taman_kehati_id: Optional[int] = None


class UserInDB(BaseUser):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    nama: str
    role: UserRoleEnum
    is_active: bool
    taman_kehati_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[UUID] = None


class TamanKehatiCreate(BaseModel):
    kode: Optional[str] = None
    nama_resmi: str
    alamat: str
    luas: Optional[float] = None
    tipe_taman: str
    tanggal_penetapan: Optional[str] = None
    deskripsi: Optional[str] = None
    provinsi_id: int
    kabupaten_kota_id: int
    kecamatan_id: Optional[int] = None
    desa_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    batas_area: Optional[dict] = None  # GeoJSON polygon


class TamanKehatiUpdate(BaseModel):
    kode: Optional[str] = None
    nama_resmi: Optional[str] = None
    alamat: Optional[str] = None
    luas: Optional[float] = None
    tipe_taman: Optional[str] = None
    tanggal_penetapan: Optional[str] = None
    deskripsi: Optional[str] = None
    provinsi_id: Optional[int] = None
    kabupaten_kota_id: Optional[int] = None
    kecamatan_id: Optional[int] = None
    desa_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    batas_area: Optional[dict] = None  # GeoJSON polygon
    status: Optional[StatusPublikasiEnum] = None


class TamanKehatiResponse(BaseModel):
    id: int
    kode: Optional[str]
    namaResmi: str = Field(alias="nama_resmi")
    alamat: str
    luas: Optional[float]
    tipeTaman: str = Field(alias="tipe_taman")
    tanggalPenetapan: Optional[str] = Field(alias="tanggal_penetapan")
    deskripsi: Optional[str]
    provinsi_id: int
    kabupaten_kota_id: int
    kecamatan_id: Optional[int]
    desa_id: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    status: StatusPublikasiEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True