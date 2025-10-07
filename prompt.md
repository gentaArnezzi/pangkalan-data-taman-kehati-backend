# prompt.md — Taman Kehati API Refactor & Extension (Strict PRD-Aligned)

## Purpose

You are an AI code generator/refactor agent. Your task is to **modify and extend an existing FastAPI + PostgreSQL/PostGIS codebase** (“Taman Kehati API”) so it strictly aligns with the product scope and priority described below, **without deviating from the PRD**. You must:

1. Fix incorrect implementations.
2. Add missing features required for the MVP and next phases.
3. Preserve working parts unless they conflict with the PRD or security/quality requirements.
4. Produce a complete, runnable project with tests, OpenAPI docs, and Docker support.

## Source of Truth

1. The existing project already contains:

- FastAPI app with routers: `auth`, `users`, `taman_kehati`, `koleksi_tumbuhan`, `data_export`
- Async SQLAlchemy, JWT/bcrypt, PostGIS via geoalchemy2, page views, search index, audit log, media management.
- Roles currently in use: `super_admin`, `admin_taman`, `viewer`.
- Geo-masking for non-admin users is present.

2. You must enforce and not deviate from the following PRD guardrails (interpretation only; do not invent new product scope):

- Public portal: national interactive map of parks, directory of parks, park detail pages with gallery and (phase 2) zone polygons, searchable plant database, detailed plant pages with morphology, ecology, provenance, and coordinates.
- Admin portal: CRUD for parks and plant collections, media upload, zone polygon management (draw/upload GeoJSON), linkage of collections to zones.
- MVP priority (Phase 1): public portal for directory + park and collection details (without per-zone polygons), admin CRUD for park and collections, national distribution map; later phases: zone layers, advanced collection search, data export, articles/news module, and further integrations.

## Don’ts (Hard Constraints)

- Do not change the fundamental domain model or introduce new top-level entities not present in the database schema.
- Do not remove or bypass existing security (JWT, RBAC) or geospatial masking unless replacing with a more correct implementation that passes stricter tests.
- Do not diverge from the role model used by the current codebase (`super_admin`, `admin_taman`, `viewer`).
- Do not break existing migrations or data; all schema changes must be additive and versioned via Alembic, and only when absolutely necessary.
- Do not invent UI; deliver API capabilities only, with OpenAPI examples suitable for React/Next.js + Leaflet/Mapbox consumption.

## High-Level Technical Targets

- Language/Framework: Python 3.12, FastAPI, SQLAlchemy 2.x async, asyncpg, Pydantic v2.
- Database: PostgreSQL + PostGIS (SRID 4326).
- Auth: JWT access + refresh, bcrypt_sha256 password hashing (passlib).
- CORS configurable.
- Logging: structured JSON logs, request/response timing, correlation id.
- Observability: `/health` endpoint validates DB connection, PostGIS availability, and FTS readiness.

## Architecture & Folder Layout (enforce/repair)

```
app/
  main.py
  settings.py
  database.py
  deps.py
  auth/            # jwt utils, password hashing, dependency for current_user, RBAC
  api/routers/     # one module per resource (auth, users, taman, zona, koleksi, media, artikel, search, views, audit, meta, export)
  models/          # SQLAlchemy models reflecting the DB
  schemas/         # Pydantic v2
  services/        # business logic (geo masking, search, stats, media abstraction)
  repositories/    # data access layer
  search/          # FTS utilities
  geo/             # GeoJSON serializers, SRID validators, polygon ring checks
  media/           # storage adapters (local)
  audit/           # audit log writer
  utils/
migrations/
tests/
```

If a module exists with another path/name, **migrate to the structure above** with minimal disruption and clear commit messages.

## RBAC and Multi-Tenancy Scope

- Roles: `super_admin` (global), `admin_taman` (scoped to one or more parks), `viewer` (public read).
- Enforce per-resource permissions:

  - viewer: read only published/public resources.
  - admin_taman: CRUD only for resources under their `taman_kehati_id`.
  - super_admin: full CRUD, user and role management, system operations (reindex, exports).

- All mutating endpoints must write to `audit_log` with `{user_id, action, table_name, record_id, old_data, new_data, ip_address, user_agent, created_at}`.

## Geospatial Requirements

- All geometry I/O uses **GeoJSON**; internally, SRID must be 4326.
- Provide separate “/geo” read endpoints for heavy geometry (park polygons, zone polygons), returning Feature/FeatureCollection.
- Implement geo-filters where relevant: `geoWithin`, `geoIntersects`, and “near” queries for points.
- Keep **coordinate masking** active for non-admin users for sensitive points (configurable precision truncation or offset jitter); make this deterministic per resource id to avoid “moving targets” across requests.
- Validate polygon ring orientation and SRID on write; reject invalid uploads with explicit error payloads.

## HTTP Contract Conventions

- Pagination: `page` (1-based), `size` (default 20, max 100).
- Sorting: `sort=field,-field`.
- Sparse fields: `?fields=a,b,c`.
- Light includes: `?include=media_main,taman,zona,author` (only joins allowed by performance budget).
- Filters: `filter[field].op=value` with ops: `eq`, `ilike`, `in`, `range`, `null`, `geoWithin`, `geoIntersects`.
- Caching: ETag on GET detail/list; support `If-None-Match`.
- Optimistic concurrency: `If-Match` required on PATCH; compare with server‐side `updated_at`.

# database now

postgres=> \d artikel
\d audit_log
\d desa
\d kabupaten_kota
\d kecamatan
\d koleksi_tumbuhan
\d media
\d page_views
\d provinsi
\d search_index
\d spatial_ref_sys
\d taman_kehati
\d users
\d zona_taman
                                           Table "public.artikel"
     Column      |            Type             | Collation | Nullable |               Default               
-----------------+-----------------------------+-----------+----------+-------------------------------------
 id              | integer                     |           | not null | nextval('artikel_id_seq'::regclass)
 judul           | character varying(255)      |           | not null | 
 slug            | character varying(300)      |           | not null | 
 ringkasan       | text                        |           |          | 
 konten          | text                        |           | not null | 
 cover_image_id  | integer                     |           |          | 
 taman_kehati_id | integer                     |           |          | 
 kategori        | character varying(50)       |           |          | 
 tags            | jsonb                       |           |          | 
 status          | status_publikasi            |           | not null | 'draft'::status_publikasi
 published_at    | timestamp without time zone |           |          | 
 author_id       | uuid                        |           | not null | 
 created_at      | timestamp without time zone |           | not null | now()
 updated_at      | timestamp without time zone |           | not null | now()
Indexes:
    "artikel_pkey" PRIMARY KEY, btree (id)
    "artikel_published_idx" btree (published_at)
    "artikel_slug_idx" btree (slug)
    "artikel_slug_unique" UNIQUE CONSTRAINT, btree (slug)
    "artikel_status_idx" btree (status)
    "artikel_taman_idx" btree (taman_kehati_id)
Foreign-key constraints:
    "artikel_author_id_users_id_fk" FOREIGN KEY (author_id) REFERENCES users(id)
    "artikel_cover_image_id_media_id_fk" FOREIGN KEY (cover_image_id) REFERENCES media(id)
    "artikel_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)

Table "public.audit_log"
   Column   |            Type             | Collation | Nullable |                Default                
------------+-----------------------------+-----------+----------+---------------------------------------
 id         | integer                     |           | not null | nextval('audit_log_id_seq'::regclass)
 user_id    | uuid                        |           |          | 
 action     | character varying(50)       |           | not null | 
 table_name | character varying(50)       |           | not null | 
 record_id  | integer                     |           |          | 
 old_data   | jsonb                       |           |          | 
 new_data   | jsonb                       |           |          | 
 ip_address | character varying(45)       |           |          | 
 user_agent | text                        |           |          | 
 created_at | timestamp without time zone |           | not null | now()
Indexes:
    "audit_log_pkey" PRIMARY KEY, btree (id)
    "audit_action_idx" btree (action)
    "audit_date_idx" btree (created_at)
    "audit_table_idx" btree (table_name)
    "audit_user_idx" btree (user_id)
Foreign-key constraints:
    "audit_log_user_id_users_id_fk" FOREIGN KEY (user_id) REFERENCES users(id)

Table "public.desa"
    Column    |            Type             | Collation | Nullable |             Default              
--------------+-----------------------------+-----------+----------+----------------------------------
 id           | integer                     |           | not null | nextval('desa_id_seq'::regclass)
 kecamatan_id | integer                     |           |          | 
 kode         | character varying(15)       |           | not null | 
 nama         | character varying(100)      |           | not null | 
 created_at   | timestamp without time zone |           | not null | now()
 updated_at   | timestamp without time zone |           | not null | now()
Indexes:
    "desa_pkey" PRIMARY KEY, btree (id)
    "desa_kode_unique" UNIQUE CONSTRAINT, btree (kode)
Foreign-key constraints:
    "desa_kecamatan_id_kecamatan_id_fk" FOREIGN KEY (kecamatan_id) REFERENCES kecamatan(id)
Referenced by:
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_asal_desa_id_desa_id_fk" FOREIGN KEY (asal_desa_id) REFERENCES desa(id)
    TABLE "taman_kehati" CONSTRAINT "taman_kehati_desa_id_desa_id_fk" FOREIGN KEY (desa_id) REFERENCES desa(id)

Table "public.kabupaten_kota"
   Column    |            Type             | Collation | Nullable |                  Default                   
-------------+-----------------------------+-----------+----------+--------------------------------------------
 id          | integer                     |           | not null | nextval('kabupaten_kota_id_seq'::regclass)
 provinsi_id | integer                     |           |          | 
 kode        | character varying(10)       |           | not null | 
 nama        | character varying(100)      |           | not null | 
 tipe        | character varying(20)       |           |          | 
 created_at  | timestamp without time zone |           | not null | now()
 updated_at  | timestamp without time zone |           | not null | now()
Indexes:
    "kabupaten_kota_pkey" PRIMARY KEY, btree (id)
    "kabupaten_kota_kode_unique" UNIQUE CONSTRAINT, btree (kode)
Foreign-key constraints:
    "kabupaten_kota_provinsi_id_provinsi_id_fk" FOREIGN KEY (provinsi_id) REFERENCES provinsi(id)
Referenced by:
    TABLE "kecamatan" CONSTRAINT "kecamatan_kabupaten_kota_id_kabupaten_kota_id_fk" FOREIGN KEY (kabupaten_kota_id) REFERENCES kabupaten_kota(id)
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_asal_kabupaten_id_kabupaten_kota_id_fk" FOREIGN KEY (asal_kabupaten_id) REFERENCES kabupaten_kota(id)
    TABLE "taman_kehati" CONSTRAINT "taman_kehati_kabupaten_kota_id_kabupaten_kota_id_fk" FOREIGN KEY (kabupaten_kota_id) REFERENCES kabupaten_kota(id)

Table "public.kecamatan"
      Column       |            Type             | Collation | Nullable |                Default                
-------------------+-----------------------------+-----------+----------+---------------------------------------
 id                | integer                     |           | not null | nextval('kecamatan_id_seq'::regclass)
 kabupaten_kota_id | integer                     |           |          | 
 kode              | character varying(10)       |           | not null | 
 nama              | character varying(100)      |           | not null | 
 created_at        | timestamp without time zone |           | not null | now()
 updated_at        | timestamp without time zone |           | not null | now()
Indexes:
    "kecamatan_pkey" PRIMARY KEY, btree (id)
    "kecamatan_kode_unique" UNIQUE CONSTRAINT, btree (kode)
Foreign-key constraints:
    "kecamatan_kabupaten_kota_id_kabupaten_kota_id_fk" FOREIGN KEY (kabupaten_kota_id) REFERENCES kabupaten_kota(id)
Referenced by:
    TABLE "desa" CONSTRAINT "desa_kecamatan_id_kecamatan_id_fk" FOREIGN KEY (kecamatan_id) REFERENCES kecamatan(id)
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_asal_kecamatan_id_kecamatan_id_fk" FOREIGN KEY (asal_kecamatan_id) REFERENCES kecamatan(id)
    TABLE "taman_kehati" CONSTRAINT "taman_kehati_kecamatan_id_kecamatan_id_fk" FOREIGN KEY (kecamatan_id) REFERENCES kecamatan(id)

Table "public.koleksi_tumbuhan"
        Column        |            Type             | Collation | Nullable |                   Default                    
----------------------+-----------------------------+-----------+----------+----------------------------------------------
 id                   | integer                     |           | not null | nextval('koleksi_tumbuhan_id_seq'::regclass)
 nomor_koleksi        | character varying(100)      |           |          | 
 nama_lokal_daerah    | character varying(255)      |           |          | 
 nama_umum_nasional   | character varying(255)      |           |          | 
 nama_ilmiah          | character varying(255)      |           | not null | 
 genus                | character varying(100)      |           |          | 
 spesies              | character varying(100)      |           |          | 
 author               | character varying(255)      |           |          | 
 sumber_publikasi     | text                        |           |          | 
 bentuk_pohon         | text                        |           |          | 
 bentuk_daun          | text                        |           |          | 
 bentuk_bunga         | text                        |           |          | 
 bentuk_buah          | text                        |           |          | 
 waktu_berbunga       | character varying(100)      |           |          | 
 waktu_berbuah        | character varying(100)      |           |          | 
 taman_kehati_id      | integer                     |           | not null | 
 zona_id              | integer                     |           |          | 
 latitude_taman       | numeric(10,8)               |           |          | 
 longitude_taman      | numeric(11,8)               |           |          | 
 koordinat_taman      | geometry(Point,4326)        |           |          | 
 ketinggian_taman     | integer                     |           |          | 
 asal_kampung         | character varying(100)      |           |          | 
 asal_desa_id         | integer                     |           |          | 
 asal_kecamatan_id    | integer                     |           |          | 
 asal_kabupaten_id    | integer                     |           |          | 
 asal_provinsi_id     | integer                     |           |          | 
 latitude_asal        | numeric(10,8)               |           |          | 
 longitude_asal       | numeric(11,8)               |           |          | 
 koordinat_asal       | geometry(Point,4326)        |           |          | 
 ketinggian_asal      | integer                     |           |          | 
 sebaran_global       | text                        |           |          | 
 referensi_sebaran    | text                        |           |          | 
 status_endemik       | status_endemik              |           |          | 'tidak_diketahui'::status_endemik
 habitat_alami        | text                        |           |          | 
 referensi_habitat    | text                        |           |          | 
 metode_perbanyakan   | text                        |           |          | 
 manfaat_masyarakat   | text                        |           |          | 
 manfaat_lingkungan   | text                        |           |          | 
 potensi_pengembangan | text                        |           |          | 
 tanggal_pengumpulan  | date                        |           |          | 
 tanggal_penanaman    | date                        |           |          | 
 status               | status_publikasi            |           | not null | 'draft'::status_publikasi
 created_by           | uuid                        |           |          | 
 updated_by           | uuid                        |           |          | 
 created_at           | timestamp without time zone |           | not null | now()
 updated_at           | timestamp without time zone |           | not null | now()
Indexes:
    "koleksi_tumbuhan_pkey" PRIMARY KEY, btree (id)
    "koleksi_endemik_idx" btree (status_endemik)
    "koleksi_koordinat_asal_idx" gist (koordinat_asal)
    "koleksi_koordinat_taman_idx" gist (koordinat_taman)
    "koleksi_nama_ilmiah_idx" btree (nama_ilmiah)
    "koleksi_taman_idx" btree (taman_kehati_id)
    "koleksi_tumbuhan_nomor_koleksi_unique" UNIQUE CONSTRAINT, btree (nomor_koleksi)
    "koleksi_zona_idx" btree (zona_id)
Foreign-key constraints:
    "koleksi_tumbuhan_asal_desa_id_desa_id_fk" FOREIGN KEY (asal_desa_id) REFERENCES desa(id)
    "koleksi_tumbuhan_asal_kabupaten_id_kabupaten_kota_id_fk" FOREIGN KEY (asal_kabupaten_id) REFERENCES kabupaten_kota(id)
    "koleksi_tumbuhan_asal_kecamatan_id_kecamatan_id_fk" FOREIGN KEY (asal_kecamatan_id) REFERENCES kecamatan(id)
    "koleksi_tumbuhan_asal_provinsi_id_provinsi_id_fk" FOREIGN KEY (asal_provinsi_id) REFERENCES provinsi(id)
    "koleksi_tumbuhan_created_by_users_id_fk" FOREIGN KEY (created_by) REFERENCES users(id)
    "koleksi_tumbuhan_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
    "koleksi_tumbuhan_updated_by_users_id_fk" FOREIGN KEY (updated_by) REFERENCES users(id)
    "koleksi_tumbuhan_zona_id_zona_taman_id_fk" FOREIGN KEY (zona_id) REFERENCES zona_taman(id)
Referenced by:
    TABLE "media" CONSTRAINT "media_koleksi_tumbuhan_id_koleksi_tumbuhan_id_fk" FOREIGN KEY (koleksi_tumbuhan_id) REFERENCES koleksi_tumbuhan(id)
    TABLE "page_views" CONSTRAINT "page_views_koleksi_tumbuhan_id_koleksi_tumbuhan_id_fk" FOREIGN KEY (koleksi_tumbuhan_id) REFERENCES koleksi_tumbuhan(id)
    TABLE "search_index" CONSTRAINT "search_index_koleksi_tumbuhan_id_koleksi_tumbuhan_id_fk" FOREIGN KEY (koleksi_tumbuhan_id) REFERENCES koleksi_tumbuhan(id)

Table "public.media"
       Column        |            Type             | Collation | Nullable |              Default              
---------------------+-----------------------------+-----------+----------+-----------------------------------
 id                  | integer                     |           | not null | nextval('media_id_seq'::regclass)
 taman_kehati_id     | integer                     |           |          | 
 koleksi_tumbuhan_id | integer                     |           |          | 
 media_type          | media_type                  |           | not null | 
 media_category      | media_category              |           | not null | 
 file_name           | character varying(255)      |           | not null | 
 file_path           | character varying(500)      |           | not null | 
 file_size           | integer                     |           |          | 
 mime_type           | character varying(100)      |           |          | 
 caption             | text                        |           |          | 
 is_main_image       | boolean                     |           |          | false
 uploaded_by         | uuid                        |           |          | 
 created_at          | timestamp without time zone |           | not null | now()
Indexes:
    "media_pkey" PRIMARY KEY, btree (id)
    "media_koleksi_idx" btree (koleksi_tumbuhan_id)
    "media_main_idx" btree (is_main_image)
    "media_taman_idx" btree (taman_kehati_id)
Foreign-key constraints:
    "media_koleksi_tumbuhan_id_koleksi_tumbuhan_id_fk" FOREIGN KEY (koleksi_tumbuhan_id) REFERENCES koleksi_tumbuhan(id)
    "media_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
    "media_uploaded_by_users_id_fk" FOREIGN KEY (uploaded_by) REFERENCES users(id)
Referenced by:
    TABLE "artikel" CONSTRAINT "artikel_cover_image_id_media_id_fk" FOREIGN KEY (cover_image_id) REFERENCES media(id)

Table "public.page_views"
       Column        |            Type             | Collation | Nullable |                Default                 
---------------------+-----------------------------+-----------+----------+----------------------------------------
 id                  | integer                     |           | not null | nextval('page_views_id_seq'::regclass)
 taman_kehati_id     | integer                     |           |          | 
 koleksi_tumbuhan_id | integer                     |           |          | 
 page_type           | character varying(50)       |           | not null | 
 ip_address          | character varying(45)       |           |          | 
 user_agent          | text                        |           |          | 
 referrer            | text                        |           |          | 
 session_id          | character varying(100)      |           |          | 
 created_at          | timestamp without time zone |           | not null | now()
Indexes:
    "page_views_pkey" PRIMARY KEY, btree (id)
    "views_date_idx" btree (created_at)
    "views_koleksi_idx" btree (koleksi_tumbuhan_id)
    "views_taman_idx" btree (taman_kehati_id)
Foreign-key constraints:
    "page_views_koleksi_tumbuhan_id_koleksi_tumbuhan_id_fk" FOREIGN KEY (koleksi_tumbuhan_id) REFERENCES koleksi_tumbuhan(id)
    "page_views_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)

Table "public.provinsi"
   Column   |            Type             | Collation | Nullable |               Default                
------------+-----------------------------+-----------+----------+--------------------------------------
 id         | integer                     |           | not null | nextval('provinsi_id_seq'::regclass)
 kode       | character varying(10)       |           | not null | 
 nama       | character varying(100)      |           | not null | 
 pulau      | character varying(50)       |           |          | 
 created_at | timestamp without time zone |           | not null | now()
 updated_at | timestamp without time zone |           | not null | now()
Indexes:
    "provinsi_pkey" PRIMARY KEY, btree (id)
    "provinsi_kode_unique" UNIQUE CONSTRAINT, btree (kode)
Referenced by:
    TABLE "kabupaten_kota" CONSTRAINT "kabupaten_kota_provinsi_id_provinsi_id_fk" FOREIGN KEY (provinsi_id) REFERENCES provinsi(id)
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_asal_provinsi_id_provinsi_id_fk" FOREIGN KEY (asal_provinsi_id) REFERENCES provinsi(id)
    TABLE "taman_kehati" CONSTRAINT "taman_kehati_provinsi_id_provinsi_id_fk" FOREIGN KEY (provinsi_id) REFERENCES provinsi(id)

Table "public.search_index"
       Column        |            Type             | Collation | Nullable |                 Default                  
---------------------+-----------------------------+-----------+----------+------------------------------------------
 id                  | integer                     |           | not null | nextval('search_index_id_seq'::regclass)
 taman_kehati_id     | integer                     |           |          | 
 koleksi_tumbuhan_id | integer                     |           |          | 
 searchable_text     | text                        |           | not null | 
 entity_type         | character varying(20)       |           | not null | 
 updated_at          | timestamp without time zone |           | not null | now()
Indexes:
    "search_index_pkey" PRIMARY KEY, btree (id)
    "search_fulltext_idx" gin (to_tsvector('indonesian'::regconfig, searchable_text))
    "search_koleksi_idx" btree (koleksi_tumbuhan_id)
    "search_taman_idx" btree (taman_kehati_id)
Foreign-key constraints:
    "search_index_koleksi_tumbuhan_id_koleksi_tumbuhan_id_fk" FOREIGN KEY (koleksi_tumbuhan_id) REFERENCES koleksi_tumbuhan(id)
    "search_index_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)

Table "public.spatial_ref_sys"
  Column   |          Type           | Collation | Nullable | Default 
-----------+-------------------------+-----------+----------+---------
 srid      | integer                 |           | not null | 
 auth_name | character varying(256)  |           |          | 
 auth_srid | integer                 |           |          | 
 srtext    | character varying(2048) |           |          | 
 proj4text | character varying(2048) |           |          | 
Indexes:
    "spatial_ref_sys_pkey" PRIMARY KEY, btree (srid)
Check constraints:
    "spatial_ref_sys_srid_check" CHECK (srid > 0 AND srid <= 998999)

Table "public.taman_kehati"
      Column       |            Type             | Collation | Nullable |                 Default                  
-------------------+-----------------------------+-----------+----------+------------------------------------------
 id                | integer                     |           | not null | nextval('taman_kehati_id_seq'::regclass)
 kode              | character varying(50)       |           |          | 
 nama_resmi        | character varying(255)      |           | not null | 
 alamat            | text                        |           | not null | 
 luas              | numeric(10,2)               |           |          | 
 tipe_taman        | tipe_taman                  |           | not null | 
 tanggal_penetapan | date                        |           |          | 
 deskripsi         | text                        |           |          | 
 provinsi_id       | integer                     |           | not null | 
 kabupaten_kota_id | integer                     |           | not null | 
 kecamatan_id      | integer                     |           |          | 
 desa_id           | integer                     |           |          | 
 latitude          | numeric(10,8)               |           |          | 
 longitude         | numeric(11,8)               |           |          | 
 koordinat         | geometry(Point,4326)        |           |          | 
 batas_area        | geometry(Polygon,4326)      |           |          | 
 status            | status_publikasi            |           | not null | 'draft'::status_publikasi
 created_by        | uuid                        |           |          | 
 updated_by        | uuid                        |           |          | 
 created_at        | timestamp without time zone |           | not null | now()
 updated_at        | timestamp without time zone |           | not null | now()
Indexes:
    "taman_kehati_pkey" PRIMARY KEY, btree (id)
    "taman_kehati_batas_idx" gist (batas_area)
    "taman_kehati_kode_unique" UNIQUE CONSTRAINT, btree (kode)
    "taman_kehati_koordinat_idx" gist (koordinat)
    "taman_kehati_nama_idx" btree (nama_resmi)
    "taman_kehati_provinsi_idx" btree (provinsi_id)
    "taman_kehati_status_idx" btree (status)
Foreign-key constraints:
    "taman_kehati_created_by_users_id_fk" FOREIGN KEY (created_by) REFERENCES users(id)
    "taman_kehati_desa_id_desa_id_fk" FOREIGN KEY (desa_id) REFERENCES desa(id)
    "taman_kehati_kabupaten_kota_id_kabupaten_kota_id_fk" FOREIGN KEY (kabupaten_kota_id) REFERENCES kabupaten_kota(id)
    "taman_kehati_kecamatan_id_kecamatan_id_fk" FOREIGN KEY (kecamatan_id) REFERENCES kecamatan(id)
    "taman_kehati_provinsi_id_provinsi_id_fk" FOREIGN KEY (provinsi_id) REFERENCES provinsi(id)
    "taman_kehati_updated_by_users_id_fk" FOREIGN KEY (updated_by) REFERENCES users(id)
Referenced by:
    TABLE "artikel" CONSTRAINT "artikel_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
    TABLE "media" CONSTRAINT "media_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
    TABLE "page_views" CONSTRAINT "page_views_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
    TABLE "search_index" CONSTRAINT "search_index_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
    TABLE "users" CONSTRAINT "users_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
    TABLE "zona_taman" CONSTRAINT "zona_taman_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)

Table "public.users"
     Column      |            Type             | Collation | Nullable |       Default       
-----------------+-----------------------------+-----------+----------+---------------------
 id              | uuid                        |           | not null | gen_random_uuid()
 email           | character varying(255)      |           | not null | 
 password        | character varying(255)      |           | not null | 
 nama            | character varying(255)      |           | not null | 
 role            | user_role                   |           | not null | 'viewer'::user_role
 is_active       | boolean                     |           | not null | true
 taman_kehati_id | integer                     |           |          | 
 created_at      | timestamp without time zone |           | not null | now()
 updated_at      | timestamp without time zone |           | not null | now()
Indexes:
    "users_pkey" PRIMARY KEY, btree (id)
    "users_email_idx" btree (email)
    "users_email_unique" UNIQUE CONSTRAINT, btree (email)
    "users_taman_idx" btree (taman_kehati_id)
Foreign-key constraints:
    "users_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
Referenced by:
    TABLE "artikel" CONSTRAINT "artikel_author_id_users_id_fk" FOREIGN KEY (author_id) REFERENCES users(id)
    TABLE "audit_log" CONSTRAINT "audit_log_user_id_users_id_fk" FOREIGN KEY (user_id) REFERENCES users(id)
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_created_by_users_id_fk" FOREIGN KEY (created_by) REFERENCES users(id)
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_updated_by_users_id_fk" FOREIGN KEY (updated_by) REFERENCES users(id)
    TABLE "media" CONSTRAINT "media_uploaded_by_users_id_fk" FOREIGN KEY (uploaded_by) REFERENCES users(id)
    TABLE "taman_kehati" CONSTRAINT "taman_kehati_created_by_users_id_fk" FOREIGN KEY (created_by) REFERENCES users(id)
    TABLE "taman_kehati" CONSTRAINT "taman_kehati_updated_by_users_id_fk" FOREIGN KEY (updated_by) REFERENCES users(id)

Table "public.zona_taman"
     Column      |            Type             | Collation | Nullable |                Default                 
-----------------+-----------------------------+-----------+----------+----------------------------------------
 id              | integer                     |           | not null | nextval('zona_taman_id_seq'::regclass)
 taman_kehati_id | integer                     |           | not null | 
 kode_zona       | character varying(50)       |           | not null | 
 nama_zona       | character varying(100)      |           |          | 
 deskripsi       | text                        |           |          | 
 luas            | numeric(10,2)               |           |          | 
 poligon         | geometry(Polygon,4326)      |           |          | 
 warna           | character varying(7)        |           |          | 
 created_at      | timestamp without time zone |           | not null | now()
 updated_at      | timestamp without time zone |           | not null | now()
Indexes:
    "zona_taman_pkey" PRIMARY KEY, btree (id)
    "taman_zona_unique" UNIQUE CONSTRAINT, btree (taman_kehati_id, kode_zona)
    "zona_poligon_idx" gist (poligon)
Foreign-key constraints:
    "zona_taman_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
Referenced by:
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_zona_id_zona_taman_id_fk" FOREIGN KEY (zona_id) REFERENCES zona_taman(id)

postgres=>

## Endpoints to Implement/Repair (keep names consistent; mount under `/api`)

### Auth & Users

- `POST /auth/register` (super_admin only)
- `POST /auth/login` → `{ access_token, refresh_token, user }`
- `POST /auth/refresh` → `{ access_token }`
- `GET  /auth/me`
- `GET  /users` (super_admin) filters by role, park scope
- `GET  /users/{id}`
- `PATCH/PUT /users/{id}` (self non-role fields; super_admin may update role/status)

### Reference Geography for Forms

- `GET /provinsi`
- `GET /kabupaten-kota?filter[provinsi_id].eq=`
- `GET /kecamatan?filter[kabupaten_kota_id].eq=`
- `GET /desa?filter[kecamatan_id].eq=`

### Parks (Taman Kehati)

- `GET /taman?filter[status].eq=&filter[provinsi_id].eq=&q=&page=&size=&sort=`
- `GET /taman/{id}`
- `GET /taman/{id}/geo` → FeatureCollection with point and polygon if available
- `GET /taman/{id}/stats` → `{ koleksi_count, artikel_count, views_7d, views_30d }`
- `GET /taman/near?lat=&lng=&radius_m=`
- `POST /taman` (admin_taman/super_admin)
- `PATCH /taman/{id}`
- `PATCH /taman/{id}/status` `{ status: 'draft'|'published' }`

### Zones (Zona Taman) — phase 2+

- `GET /zona?filter[taman_kehati_id].eq=`
- `GET /zona/{id}/geo` → GeoJSON Polygon
- `GET /zona/{id}/koleksi?filter[status].eq=&page=&size=`
- `POST /zona` | `PATCH /zona/{id}` | `DELETE /zona/{id}` (FK safety checks)
- `POST /zona/import` (GeoJSON), validate SRID/rings

### Plant Collections (Koleksi Tumbuhan)

- `GET /koleksi?filter[taman_kehati_id].eq=&filter[zona_id].eq=&filter[status].eq=&filter[status_endemik].eq=&filter[genus].eq=&filter[spesies].eq=&q=&page=&size=&sort=&fields=&include=media_main,taman,zona`
- `GET /koleksi/{id}`
- `GET /koleksi/{id}/media`
- `GET /koleksi/{id}/relations` → `{ terkait:[…], artikel_terkait:[…] }`
- `GET /koleksi/suggest?q=`
- `GET /koleksi/stats?group_by=status_endemik|genus|taman_kehati_id`
- `GET /koleksi/map-clusters?filter[taman_kehati_id].eq=&zoom=`
- `POST /koleksi` | `PATCH /koleksi/{id}`
- `PATCH /koleksi/{id}/status` `{ status }`

### Media

- `POST /media` (multipart): `file`, `media_type=image|video`, `media_category=koleksi|taman|artikel`, `koleksi_tumbuhan_id?`, `taman_kehati_id?`
- `GET /media?filter[koleksi_tumbuhan_id].eq=&filter[taman_kehati_id].eq=&filter[is_main_image].eq=`
- `PATCH /media/{id}` (caption, is_main_image)
- `DELETE /media/{id}`
- `POST /koleksi/{id}/media/main` `{ media_id }`

### Articles — phase 3

- `GET /artikel?filter[status].eq=&filter[taman_kehati_id].eq=&filter[kategori].eq=&filter[author_id].eq=&filter[tags].in=&q=&page=&size=&sort=published_at`
- `GET /artikel/{id}` | `GET /artikel/slug/{slug}`
- `GET /artikel/{id}/related?limit=5`
- `POST /artikel` | `PATCH /artikel/{id}`
- `PATCH /artikel/{id}/publish` (sets status + published_at)
- `PATCH /artikel/{id}/cover` `{ cover_image_id }`

### Search & Analytics

- `GET /search?q=&entity=artikel|koleksi|taman&limit=20` (FTS: Indonesian regconfig)
- `GET /search/suggest?q=`
- `POST /search/reindex` (super_admin)
- `POST /views/track` `{ page_type, taman_kehati_id?, koleksi_tumbuhan_id?, referrer, user_agent, session_id }`
- `GET /views/series?entity=taman|koleksi|artikel&id=&range=7d|30d|custom&interval=day`
- `GET /views/top?entity=artikel|koleksi&filter[taman_kehati_id].eq=&range=7d&limit=10`

### Audit & Meta

- `GET /audit?filter[table_name].eq=&filter[record_id].eq=&date_from=&date_to=&page=&size=`
- `GET /meta/enums` → values for `status_publikasi`, `status_endemik`, `media_type`, `media_category`, `tipe_taman`, `user_role`
- `GET /health`

## Search Implementation

- Maintain a dedicated `search_index` table (already present).
- Index with `to_tsvector('indonesian', searchable_text)`.
- Query with `plainto_tsquery` or `websearch_to_tsquery('indonesian', :q)`.
- Keep an incremental updater service (trigger or application-level) for inserts/updates of parks/collections/articles.

## Data Export

- Keep `api/data_export.py` but modernize:

  - Export endpoints: CSV/GeoJSON for parks, zones, collections.
  - Streaming responses for large datasets.
  - RBAC: admin_taman exports own scope; super_admin exports global.

## Media Subsystem

- Local storage by default (`MEDIA_ROOT`)
- On upload: validate MIME, size, and produce deterministic file paths.
- Optional thumbnail hooks (non-blocking); if not implemented, leave stubs and tests skipped with markers.

## Quality Gates

- Static analysis: ruff + black; mypy with permissive gradual typing.
- Tests: pytest + httpx AsyncClient.
- Coverage: ≥80% on routers/services for MVP endpoints.
- OpenAPI: complete and example-rich at `/docs` and `/openapi.json`.
- Docker: production image (Python 3.12 slim), PostGIS in docker-compose, healthchecks.

## Request/Response Examples (must be present in OpenAPI)

- Provide example payloads for list/detail, search, suggest, geo endpoints, media upload (multipart), and error shapes.
- Standard error schema:

```json
{
  "error": {
    "code": "string",
    "message": "human readable",
    "details": { "field": ["issue"] }
  }
}
```

## Testing Matrix (must implement)

1. Auth: login, refresh, protected routes, RBAC denial/allow.
2. Parks: list filters, detail, geo, stats; admin_taman CRUD limited by scope; publishing transitions.
3. Zones: import validation (SRID 4326, ring orientation), CRUD constraints with FK to collections.
4. Collections: list/search/suggest, stats, cluster endpoint behavior; masking rules verified against role.
5. Media: upload, set main image, list filters.
6. Search: correctness for Indonesian tokenizer; reindex endpoint super_admin only.
7. Views: track endpoint public; series/top require admin scope; performance for rolling windows.
8. Audit: all mutating endpoints emit correct audit entries.
9. Health: DB, PostGIS, FTS checks.

## Migration & Backward Compatibility

- Use Alembic for any new columns or indexes; never destructive in MVP.
- Zero-downtime friendly migrations (create new columns/indexes, backfill, then switch).
- Provide rollback notes in migration files.

## Performance Requirements

- P95 list endpoints ≤ 300 ms for page size 20 with typical filters and includes.
- Geo endpoints may be heavier; cacheable with ETag and sensible geometry simplification for public reads.
- Add indexes when needed (FTS GIN, btree on foreign keys, GIST on geometries).

## Deliverables

- Updated source tree following the stated layout.
- Passing test suite with coverage report.
- OpenAPI 3.1 JSON and Markdown README (Quickstart: Docker Compose, `.env`, migrations).
- Postman collection exported from OpenAPI.
- Makefile targets: `dev`, `lint`, `test`, `migrate`, `seed`, `run`.
- Clear commit history; each logical change in a separate commit with message:

  - `feat(api): …`
  - `fix(rbac): …`
  - `chore(migrations): …`
  - `refactor(structure): …`
  - `test: …`

## Step-by-Step Execution Plan (the agent must follow)

1. Audit current code: list mismatches vs this specification; produce a short “gap report”.
2. Restructure to the required layout (minimal breaking changes).
3. Stabilize database connectivity (async engine, session lifecycle) and ensure PostGIS introspection works.
4. Normalize JWT and RBAC to the specified roles and scopes; keep coordinate masking.
5. Implement/repair routers and services to match all endpoints above, honoring filters, pagination, includes, sorting, ETag/If-Match.
6. Implement GeoJSON serializers and validators; add `/geo` endpoints.
7. Wire FTS search and suggest; implement reindex administrative endpoint.
8. Implement analytics endpoints and ensure `views/track` logging does not require auth.
9. Ensure all mutations write to `audit_log`.
10. Fill OpenAPI examples and generate Postman collection.
11. Add tests across the testing matrix; reach coverage target.
12. Provide Docker/Docker Compose and `Makefile`; verify `make dev` and `make test` succeed.
13. Produce a final “conformance report” mapping endpoints to PRD scope and MVP/phase boundaries.

## Acceptance Criteria

- The running API strictly matches endpoints and behavior defined here, adheres to RBAC and masking rules, returns valid GeoJSON, supports Indonesian FTS, and emits audit logs on all mutations.
- OpenAPI is accurate and exhaustive with working examples.
- Tests pass locally and in CI; coverage ≥80% on core routers/services.
- No scope creep beyond the PRD; later-phase features are scaffolded but not exposed in MVP routes unless explicitly required.
