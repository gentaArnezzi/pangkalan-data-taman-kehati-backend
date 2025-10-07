from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from uuid import UUID
from .users import StatusPublikasiEnum


class StatusEndemikEnum(str, Enum):
    endemik = "endemik"
    non_endemik = "non_endemik"
    tidak_diketahui = "tidak_diketahui"


class KoleksiTumbuhanBase(BaseModel):
    nomor_koleksi: Optional[str] = None
    nama_lokal_daerah: Optional[str] = None
    nama_umum_nasional: Optional[str] = None
    nama_ilmiah: str
    genus: Optional[str] = None
    spesies: Optional[str] = None
    author: Optional[str] = None
    sumber_publikasi: Optional[str] = None
    bentuk_pohon: Optional[str] = None
    bentuk_daun: Optional[str] = None
    bentuk_bunga: Optional[str] = None
    bentuk_buah: Optional[str] = None
    waktu_berbunga: Optional[str] = None
    waktu_berbuah: Optional[str] = None
    taman_kehati_id: int
    zona_id: Optional[int] = None
    latitude_taman: Optional[float] = None
    longitude_taman: Optional[float] = None
    ketinggian_taman: Optional[int] = None
    asal_kampung: Optional[str] = None
    asal_desa_id: Optional[int] = None
    asal_kecamatan_id: Optional[int] = None
    asal_kabupaten_id: Optional[int] = None
    asal_provinsi_id: Optional[int] = None
    latitude_asal: Optional[float] = None
    longitude_asal: Optional[float] = None
    ketinggian_asal: Optional[int] = None
    sebaran_global: Optional[str] = None
    referensi_sebaran: Optional[str] = None
    status_endemik: Optional[StatusEndemikEnum] = StatusEndemikEnum.tidak_diketahui
    habitat_alami: Optional[str] = None
    referensi_habitat: Optional[str] = None
    metode_perbanyakan: Optional[str] = None
    manfaat_masyarakat: Optional[str] = None
    manfaat_lingkungan: Optional[str] = None
    potensi_pengembangan: Optional[str] = None
    tanggal_pengumpulan: Optional[date] = None
    tanggal_penanaman: Optional[date] = None


class KoleksiTumbuhanCreate(KoleksiTumbuhanBase):
    status: Optional[StatusPublikasiEnum] = StatusPublikasiEnum.draft


class KoleksiTumbuhanUpdate(BaseModel):
    nomor_koleksi: Optional[str] = None
    nama_lokal_daerah: Optional[str] = None
    nama_umum_nasional: Optional[str] = None
    nama_ilmiah: Optional[str] = None
    genus: Optional[str] = None
    spesies: Optional[str] = None
    author: Optional[str] = None
    sumber_publikasi: Optional[str] = None
    bentuk_pohon: Optional[str] = None
    bentuk_daun: Optional[str] = None
    bentuk_bunga: Optional[str] = None
    bentuk_buah: Optional[str] = None
    waktu_berbunga: Optional[str] = None
    waktu_berbuah: Optional[str] = None
    taman_kehati_id: Optional[int] = None
    zona_id: Optional[int] = None
    latitude_taman: Optional[float] = None
    longitude_taman: Optional[float] = None
    ketinggian_taman: Optional[int] = None
    asal_kampung: Optional[str] = None
    asal_desa_id: Optional[int] = None
    asal_kecamatan_id: Optional[int] = None
    asal_kabupaten_id: Optional[int] = None
    asal_provinsi_id: Optional[int] = None
    latitude_asal: Optional[float] = None
    longitude_asal: Optional[float] = None
    ketinggian_asal: Optional[int] = None
    sebaran_global: Optional[str] = None
    referensi_sebaran: Optional[str] = None
    status_endemik: Optional[StatusEndemikEnum] = None
    habitat_alami: Optional[str] = None
    referensi_habitat: Optional[str] = None
    metode_perbanyakan: Optional[str] = None
    manfaat_masyarakat: Optional[str] = None
    manfaat_lingkungan: Optional[str] = None
    potensi_pengembangan: Optional[str] = None
    tanggal_pengumpulan: Optional[date] = None
    tanggal_penanaman: Optional[date] = None
    status: Optional[StatusPublikasiEnum] = None


class KoleksiTumbuhanResponse(BaseModel):
    id: int
    nomor_koleksi: Optional[str]
    namaLokalDaerah: Optional[str] = Field(alias="nama_lokal_daerah")
    namaUmumNasional: Optional[str] = Field(alias="nama_umum_nasional")
    namaIlmiah: str = Field(alias="nama_ilmiah")
    genus: Optional[str]
    spesies: Optional[str]
    author: Optional[str]
    sumberPublikasi: Optional[str] = Field(alias="sumber_publikasi")
    bentukPohon: Optional[str] = Field(alias="bentuk_pohon")
    bentukDaun: Optional[str] = Field(alias="bentuk_daun")
    bentukBunga: Optional[str] = Field(alias="bentuk_bunga")
    bentukBuah: Optional[str] = Field(alias="bentuk_buah")
    waktuBerbunga: Optional[str] = Field(alias="waktu_berbunga")
    waktuBerbuah: Optional[str] = Field(alias="waktu_berbuah")
    tamanKehatiId: int = Field(alias="taman_kehati_id")
    zonaId: Optional[int] = Field(alias="zona_id")
    latitudeTaman: Optional[float] = Field(alias="latitude_taman")
    longitudeTaman: Optional[float] = Field(alias="longitude_taman")
    ketinggianTaman: Optional[int] = Field(alias="ketinggian_taman")
    asalKampung: Optional[str] = Field(alias="asal_kampung")
    asalDesaId: Optional[int] = Field(alias="asal_desa_id")
    asalKecamatanId: Optional[int] = Field(alias="asal_kecamatan_id")
    asalKabupatenId: Optional[int] = Field(alias="asal_kabupaten_id")
    asalProvinsiId: Optional[int] = Field(alias="asal_provinsi_id")
    latitudeAsal: Optional[float] = Field(alias="latitude_asal")
    longitudeAsal: Optional[float] = Field(alias="longitude_asal")
    ketinggianAsal: Optional[int] = Field(alias="ketinggian_asal")
    sebaranGlobal: Optional[str] = Field(alias="sebaran_global")
    referensiSebaran: Optional[str] = Field(alias="referensi_sebaran")
    statusEndemik: StatusEndemikEnum = Field(alias="status_endemik")
    habitatAlami: Optional[str] = Field(alias="habitat_alami")
    referensiHabitat: Optional[str] = Field(alias="referensi_habitat")
    metodePerbanyakan: Optional[str] = Field(alias="metode_perbanyakan")
    manfaatMasyarakat: Optional[str] = Field(alias="manfaat_masyarakat")
    manfaatLingkungan: Optional[str] = Field(alias="manfaat_lingkungan")
    potensiPengembangan: Optional[str] = Field(alias="potensi_pengembangan")
    tanggalPengumpulan: Optional[date] = Field(alias="tanggal_pengumpulan")
    tanggalPenanaman: Optional[date] = Field(alias="tanggal_penanaman")
    status: StatusPublikasiEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KoleksiTumbuhanStatsGroup(BaseModel):
    group_value: str
    count: int


class KoleksiTumbuhanStatsResponse(BaseModel):
    results: List[KoleksiTumbuhanStatsGroup]
