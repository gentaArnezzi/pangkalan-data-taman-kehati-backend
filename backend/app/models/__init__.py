from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, Date, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import enum
from uuid import uuid4

Base = declarative_base()

# Enums
class TipeTamanEnum(enum.Enum):
    kehati_instansi = "kehati_instansi"
    kehati_sekolah = "kehati_sekolah"
    kehati_kampus = "kehati_kampus"
    kehati_perusahaan = "kehati_perusahaan"
    kehati_pemda = "kehati_pemda"
    kehati_masyarakat = "kehati_masyarakat"

class StatusEndemikEnum(enum.Enum):
    endemik = "endemik"
    non_endemik = "non_endemik"
    tidak_diketahui = "tidak_diketahui"

class UserRoleEnum(enum.Enum):
    super_admin = "super_admin"
    admin_taman = "admin_taman"
    viewer = "viewer"

class StatusPublikasiEnum(enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class MediaTypeEnum(enum.Enum):
    foto = "foto"
    video = "video"

class MediaCategoryEnum(enum.Enum):
    taman_umum = "taman_umum"
    tumbuhan_keseluruhan = "tumbuhan_keseluruhan"
    daun = "daun"
    bunga = "bunga"
    buah = "buah"
    batang = "batang"
    akar = "akar"
    lainnya = "lainnya"

# Provinsi model
class Provinsi(Base):
    __tablename__ = "provinsi"
    
    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(10), unique=True, nullable=False, index=True)
    nama = Column(String(100), nullable=False)
    pulau = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Kabupaten/Kota model
class KabupatenKota(Base):
    __tablename__ = "kabupaten_kota"
    
    id = Column(Integer, primary_key=True, index=True)
    provinsi_id = Column(Integer, ForeignKey("provinsi.id"))
    kode = Column(String(10), unique=True, nullable=False, index=True)
    nama = Column(String(100), nullable=False)
    tipe = Column(String(20))  # 'Kabupaten' or 'Kota'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Kecamatan model
class Kecamatan(Base):
    __tablename__ = "kecamatan"
    
    id = Column(Integer, primary_key=True, index=True)
    kabupaten_kota_id = Column(Integer, ForeignKey("kabupaten_kota.id"))
    kode = Column(String(10), unique=True, nullable=False, index=True)
    nama = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Desa model
class Desa(Base):
    __tablename__ = "desa"
    
    id = Column(Integer, primary_key=True, index=True)
    kecamatan_id = Column(Integer, ForeignKey("kecamatan.id"))
    kode = Column(String(15), unique=True, nullable=False, index=True)
    nama = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

from sqlalchemy.orm import relationship

# Users model
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nama = Column(String(255), nullable=False)
    role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.viewer)
    is_active = Column(Boolean, default=True)
    taman_kehati_id = Column(Integer, ForeignKey("taman_kehati.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    tamanKehati = relationship("TamanKehati", foreign_keys=[taman_kehati_id], back_populates="users")

# Taman Kehati model
class TamanKehati(Base):
    __tablename__ = "taman_kehati"
    
    id = Column(Integer, primary_key=True, index=True)
    kode = Column(String(50), unique=True)
    nama_resmi = Column(String(255), nullable=False, index=True)
    alamat = Column(Text, nullable=False)
    luas = Column(DECIMAL(10, 2))  # dalam hektar
    tipe_taman = Column(Enum(TipeTamanEnum), nullable=False)
    tanggal_penetapan = Column(Date)
    deskripsi = Column(Text)
    
    # Lokasi administratif
    provinsi_id = Column(Integer, ForeignKey("provinsi.id"), nullable=False, index=True)
    kabupaten_kota_id = Column(Integer, ForeignKey("kabupaten_kota.id"), nullable=False)
    kecamatan_id = Column(Integer, ForeignKey("kecamatan.id"))
    desa_id = Column(Integer, ForeignKey("desa.id"))
    
    # Geolokasi
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    koordinat = Column(Geometry("POINT", srid=4326, spatial_index=True))
    batas_area = Column(Geometry("POLYGON", srid=4326, spatial_index=True))
    
    # Metadata
    status = Column(Enum(StatusPublikasiEnum), nullable=False, default=StatusPublikasiEnum.draft, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", foreign_keys=[User.taman_kehati_id], back_populates="tamanKehati")
    provinsi = relationship("Provinsi")
    kabupatenKota = relationship("KabupatenKota")
    kecamatan = relationship("Kecamatan")
    desa = relationship("Desa")
    zonas = relationship("ZonaTaman", back_populates="taman")
    koleksis = relationship("KoleksiTumbuhan", back_populates="taman")
    medias = relationship("Media", back_populates="taman")
    artikels = relationship("Artikel", back_populates="taman")
    createdByUser = relationship("User", foreign_keys=[created_by])
    updatedByUser = relationship("User", foreign_keys=[updated_by])

# Zona Taman model
class ZonaTaman(Base):
    __tablename__ = "zona_taman"
    
    id = Column(Integer, primary_key=True, index=True)
    taman_kehati_id = Column(Integer, ForeignKey("taman_kehati.id"), nullable=False)
    kode_zona = Column(String(50), nullable=False)
    nama_zona = Column(String(100))
    deskripsi = Column(Text)
    luas = Column(DECIMAL(10, 2))  # dalam meter persegi
    poligon = Column(Geometry("POLYGON", srid=4326, spatial_index=True))
    warna = Column(String(7))  # hex color untuk visualisasi
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    taman = relationship("TamanKehati", back_populates="zonas")
    koleksis = relationship("KoleksiTumbuhan", back_populates="zona")

# Koleksi Tumbuhan model
class KoleksiTumbuhan(Base):
    __tablename__ = "koleksi_tumbuhan"
    
    id = Column(Integer, primary_key=True, index=True)
    nomor_koleksi = Column(String(100), unique=True, index=True)
    
    # Penamaan
    nama_lokal_daerah = Column(String(255))
    nama_umum_nasional = Column(String(255))
    nama_ilmiah = Column(String(255), nullable=False, index=True)
    genus = Column(String(100))
    spesies = Column(String(100))
    author = Column(String(255))
    sumber_publikasi = Column(Text)
    
    # Morfologi
    bentuk_pohon = Column(Text)
    bentuk_daun = Column(Text)
    bentuk_bunga = Column(Text)
    bentuk_buah = Column(Text)
    waktu_berbunga = Column(String(100))
    waktu_berbuah = Column(String(100))
    
    # Lokasi di Taman
    taman_kehati_id = Column(Integer, ForeignKey("taman_kehati.id"), nullable=False, index=True)
    zona_id = Column(Integer, ForeignKey("zona_taman.id"), index=True)
    latitude_taman = Column(DECIMAL(10, 8))
    longitude_taman = Column(DECIMAL(11, 8))
    koordinat_taman = Column(Geometry("POINT", srid=4326, spatial_index=True))
    ketinggian_taman = Column(Integer)  # meter dpl
    
    # Asal-usul tanaman
    asal_kampung = Column(String(100))
    asal_desa_id = Column(Integer, ForeignKey("desa.id"))
    asal_kecamatan_id = Column(Integer, ForeignKey("kecamatan.id"))
    asal_kabupaten_id = Column(Integer, ForeignKey("kabupaten_kota.id"))
    asal_provinsi_id = Column(Integer, ForeignKey("provinsi.id"))
    latitude_asal = Column(DECIMAL(10, 8))
    longitude_asal = Column(DECIMAL(11, 8))
    koordinat_asal = Column(Geometry("POINT", srid=4326, spatial_index=True))
    ketinggian_asal = Column(Integer)  # meter dpl
    
    # Informasi ekologi
    sebaran_global = Column(Text)
    referensi_sebaran = Column(Text)
    status_endemik = Column(Enum(StatusEndemikEnum), default=StatusEndemikEnum.tidak_diketahui, index=True)
    habitat_alami = Column(Text)
    referensi_habitat = Column(Text)
    
    # Budidaya & manfaat
    metode_perbanyakan = Column(Text)
    manfaat_masyarakat = Column(Text)
    manfaat_lingkungan = Column(Text)
    potensi_pengembangan = Column(Text)
    
    # Riwayat
    tanggal_pengumpulan = Column(Date)
    tanggal_penanaman = Column(Date)
    
    # Metadata
    status = Column(Enum(StatusPublikasiEnum), nullable=False, default=StatusPublikasiEnum.draft, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    taman = relationship("TamanKehati", back_populates="koleksis")
    zona = relationship("ZonaTaman", back_populates="koleksis")
    medias = relationship("Media", back_populates="koleksiTumbuhan")
    asalDesa = relationship("Desa", foreign_keys=[asal_desa_id])
    asalKecamatan = relationship("Kecamatan", foreign_keys=[asal_kecamatan_id])
    asalKabupaten = relationship("KabupatenKota", foreign_keys=[asal_kabupaten_id])
    asalProvinsi = relationship("Provinsi", foreign_keys=[asal_provinsi_id])
    createdByUser = relationship("User", foreign_keys=[created_by])
    updatedByUser = relationship("User", foreign_keys=[updated_by])

# Media model
class Media(Base):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    taman_kehati_id = Column(Integer, ForeignKey("taman_kehati.id"))
    koleksi_tumbuhan_id = Column(Integer, ForeignKey("koleksi_tumbuhan.id"))
    media_type = Column(Enum(MediaTypeEnum), nullable=False)
    media_category = Column(Enum(MediaCategoryEnum), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)  # dalam bytes
    mime_type = Column(String(100))
    caption = Column(Text)
    is_main_image = Column(Boolean, default=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    taman = relationship("TamanKehati", back_populates="medias")
    koleksiTumbuhan = relationship("KoleksiTumbuhan", back_populates="medias")
    uploadedByUser = relationship("User", foreign_keys=[uploaded_by])

# Artikel model
class Artikel(Base):
    __tablename__ = "artikel"
    
    id = Column(Integer, primary_key=True, index=True)
    judul = Column(String(255), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    ringkasan = Column(Text)
    konten = Column(Text, nullable=False)
    cover_image_id = Column(Integer, ForeignKey("media.id"))
    taman_kehati_id = Column(Integer, ForeignKey("taman_kehati.id"))
    kategori = Column(String(50))
    tags = Column(JSONB)
    status = Column(Enum(StatusPublikasiEnum), nullable=False, default=StatusPublikasiEnum.draft, index=True)
    published_at = Column(DateTime(timezone=True))
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    taman = relationship("TamanKehati", back_populates="artikels")
    coverImage = relationship("Media", foreign_keys=[cover_image_id])
    author = relationship("User", foreign_keys=[author_id])

# Page Views model
class PageViews(Base):
    __tablename__ = "page_views"
    
    id = Column(Integer, primary_key=True, index=True)
    taman_kehati_id = Column(Integer, ForeignKey("taman_kehati.id"))
    koleksi_tumbuhan_id = Column(Integer, ForeignKey("koleksi_tumbuhan.id"))
    page_type = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    referrer = Column(Text)
    session_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Audit Log model
class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer)
    old_data = Column(JSONB)
    new_data = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Search Index model
class SearchIndex(Base):
    __tablename__ = "search_index"
    
    id = Column(Integer, primary_key=True, index=True)
    taman_kehati_id = Column(Integer, ForeignKey("taman_kehati.id"))
    koleksi_tumbuhan_id = Column(Integer, ForeignKey("koleksi_tumbuhan.id"))
    searchable_text = Column(Text, nullable=False)
    entity_type = Column(String(20), nullable=False)  # 'taman' or 'koleksi'
    updated_at = Column(DateTime(timezone=True), server_default=func.now())