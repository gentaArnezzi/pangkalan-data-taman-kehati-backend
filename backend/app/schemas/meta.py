from pydantic import BaseModel
from typing import Dict, List
from enum import Enum


class StatusPublikasiEnum(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class StatusEndemikEnum(str, Enum):
    endemik = "endemik"
    non_endemik = "non_endemik"
    tidak_diketahui = "tidak_diketahui"


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


class TipeTamanEnum(str, Enum):
    kehati_instansi = "kehati_instansi"
    kehati_sekolah = "kehati_sekolah"
    kehati_kampus = "kehati_kampus"
    kehati_perusahaan = "kehati_perusahaan"
    kehati_pemda = "kehati_pemda"
    kehati_masyarakat = "kehati_masyarakat"


class UserRoleEnum(str, Enum):
    super_admin = "super_admin"
    admin_taman = "admin_taman"
    viewer = "viewer"


class MetaEnumsResponse(BaseModel):
    status_publikasi: List[str]
    status_endemik: List[str]
    media_type: List[str]
    media_category: List[str]
    tipe_taman: List[str]
    user_role: List[str]