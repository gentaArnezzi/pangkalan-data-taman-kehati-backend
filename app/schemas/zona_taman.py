from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ZonaTamanBase(BaseModel):
    taman_kehati_id: int
    kode_zona: str
    nama_zona: Optional[str] = None
    deskripsi: Optional[str] = None
    luas: Optional[float] = None
    poligon: Optional[dict] = None  # GeoJSON polygon
    warna: Optional[str] = None  # hex color


class ZonaTamanCreate(ZonaTamanBase):
    pass


class ZonaTamanUpdate(BaseModel):
    taman_kehati_id: Optional[int] = None
    kode_zona: Optional[str] = None
    nama_zona: Optional[str] = None
    deskripsi: Optional[str] = None
    luas: Optional[float] = None
    poligon: Optional[dict] = None  # GeoJSON polygon
    warna: Optional[str] = None  # hex color


class ZonaTamanResponse(BaseModel):
    id: int
    tamanKehatiId: int = Field(alias="taman_kehati_id")
    kodeZona: str = Field(alias="kode_zona")
    namaZona: Optional[str] = Field(alias="nama_zona")
    deskripsi: Optional[str]
    luas: Optional[float]
    warna: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ZonaTamanGeoResponse(BaseModel):
    type: str = "Feature"
    geometry: dict  # GeoJSON geometry
    properties: dict