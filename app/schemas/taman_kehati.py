from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from uuid import UUID
from .users import StatusPublikasiEnum


class TipeTamanEnum(str, Enum):
    kehati_instansi = "kehati_instansi"
    kehati_sekolah = "kehati_sekolah"
    kehati_kampus = "kehati_kampus"
    kehati_perusahaan = "kehati_perusahaan"
    kehati_pemda = "kehati_pemda"
    kehati_masyarakat = "kehati_masyarakat"


class ProvinsiBase(BaseModel):
    kode: str
    nama: str
    pulau: Optional[str] = None


class ProvinsiCreate(ProvinsiBase):
    pass


class ProvinsiResponse(ProvinsiBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KabupatenKotaBase(BaseModel):
    provinsi_id: int
    kode: str
    nama: str
    tipe: Optional[str] = None  # 'Kabupaten' or 'Kota'


class KabupatenKotaCreate(KabupatenKotaBase):
    pass


class KabupatenKotaResponse(KabupatenKotaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KecamatanBase(BaseModel):
    kabupaten_kota_id: int
    kode: str
    nama: str


class KecamatanCreate(KecamatanBase):
    pass


class KecamatanResponse(KecamatanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DesaBase(BaseModel):
    kecamatan_id: int
    kode: str
    nama: str


class DesaCreate(DesaBase):
    pass


class DesaResponse(DesaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TamanKehatiBase(BaseModel):
    kode: Optional[str] = None
    nama_resmi: str
    alamat: str
    luas: Optional[float] = None
    tipe_taman: TipeTamanEnum
    tanggal_penetapan: Optional[str] = None
    deskripsi: Optional[str] = None
    provinsi_id: int
    kabupaten_kota_id: int
    kecamatan_id: Optional[int] = None
    desa_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    batas_area: Optional[dict] = None  # GeoJSON polygon


class TamanKehatiCreate(TamanKehatiBase):
    status: Optional[StatusPublikasiEnum] = StatusPublikasiEnum.draft


class TamanKehatiUpdate(BaseModel):
    kode: Optional[str] = None
    nama_resmi: Optional[str] = None
    alamat: Optional[str] = None
    luas: Optional[float] = None
    tipe_taman: Optional[TipeTamanEnum] = None
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
    tipeTaman: TipeTamanEnum = Field(alias="tipe_taman")
    tanggalPenetapan: Optional[date] = Field(alias="tanggal_penetapan")
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
    provinsi: Optional[ProvinsiResponse] = None
    kabupatenKota: Optional[KabupatenKotaResponse] = Field(alias="kabupaten_kota", default=None)

    class Config:
        from_attributes = True


class TamanKehatiGeoResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[dict]  # List of GeoJSON features


class TamanKehatiStatsResponse(BaseModel):
    koleksi_count: int
    artikel_count: int
    views_7d: int
    views_30d: int