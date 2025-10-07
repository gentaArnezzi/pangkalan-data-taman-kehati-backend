~ main*                                                                                                                                                                                                                                                                                                                                                                                                                 16:33:51
❯ clear




























































































































~ main*                                                                                                                                                                                                                                                                                                                                                                                                                 16:33:53
❯ \d artikel
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

~ main*                                                                                                                                                                                                                                                                                                                                                                                                                 16:33:54
❯ \d artikel
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

~ main*                                                                                                                                                                                                                                                                                                                                                                                                                 16:34:04
❯ \d artikel
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

~ main*                                                                                                                                                                                                                                                                                                                                                                                                                 16:34:11
❯ psql -h aws-1-ap-southeast-1.pooler.supabase.com -p 5432 -d postgres -U postgres.zpyzppqjsjbsyglejeni
Password for user postgres.zpyzppqjsjbsyglejeni: 
psql (17.6 (Homebrew))
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, compression: off, ALPN: none)
Type "help" for help.

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
     Column      |            Type             | Collation | Nullable |               Default               
-----------------+-----------------------------+-----------+----------+-------------------------------------
 id              | integer                     |           | not null | nextval('artikel_id_seq'::regclass)
 judul           | character varying(255)      |           | not null | 
 slug            | character varying(300)      |           | not null | 
 ringkasan       | text                        |           |          | 
 konten          | text                        |           | not null | 
 cover_image_id  | integer                     |           |          | 
 taman_kehati_id | integer                     |           |          | 
 kategori        | character varying(50)       |           |          | 
 tags            | jsonb                       |           |          | 
 status          | status_publikasi            |           | not null | 'draft'::status_publikasi
 published_at    | timestamp without time zone |           |          | 
 author_id       | uuid                        |           | not null | 
 created_at      | timestamp without time zone |           | not null | now()
 updated_at      | timestamp without time zone |           | not null | now()
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
   Column   |            Type             | Collation | Nullable |                Default                
------------+-----------------------------+-----------+----------+---------------------------------------
 id         | integer                     |           | not null | nextval('audit_log_id_seq'::regclass)
 user_id    | uuid                        |           |          | 
 action     | character varying(50)       |           | not null | 
 table_name | character varying(50)       |           | not null | 
 record_id  | integer                     |           |          | 
 old_data   | jsonb                       |           |          | 
 new_data   | jsonb                       |           |          | 
 ip_address | character varying(45)       |           |          | 
 user_agent | text                        |           |          | 
 created_at | timestamp without time zone |           | not null | now()
Indexes:
    "audit_log_pkey" PRIMARY KEY, btree (id)
    "audit_action_idx" btree (action)
    "audit_date_idx" btree (created_at)
    "audit_table_idx" btree (table_name)
    "audit_user_idx" btree (user_id)
Foreign-key constraints:
    "audit_log_user_id_users_id_fk" FOREIGN KEY (user_id) REFERENCES users(id)

                                         Table "public.desa"
    Column    |            Type             | Collation | Nullable |             Default              
--------------+-----------------------------+-----------+----------+----------------------------------
 id           | integer                     |           | not null | nextval('desa_id_seq'::regclass)
 kecamatan_id | integer                     |           |          | 
 kode         | character varying(15)       |           | not null | 
 nama         | character varying(100)      |           | not null | 
 created_at   | timestamp without time zone |           | not null | now()
 updated_at   | timestamp without time zone |           | not null | now()
Indexes:
    "desa_pkey" PRIMARY KEY, btree (id)
    "desa_kode_unique" UNIQUE CONSTRAINT, btree (kode)
Foreign-key constraints:
    "desa_kecamatan_id_kecamatan_id_fk" FOREIGN KEY (kecamatan_id) REFERENCES kecamatan(id)
Referenced by:
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_asal_desa_id_desa_id_fk" FOREIGN KEY (asal_desa_id) REFERENCES desa(id)
    TABLE "taman_kehati" CONSTRAINT "taman_kehati_desa_id_desa_id_fk" FOREIGN KEY (desa_id) REFERENCES desa(id)

                                         Table "public.kabupaten_kota"
   Column    |            Type             | Collation | Nullable |                  Default                   
-------------+-----------------------------+-----------+----------+--------------------------------------------
 id          | integer                     |           | not null | nextval('kabupaten_kota_id_seq'::regclass)
 provinsi_id | integer                     |           |          | 
 kode        | character varying(10)       |           | not null | 
 nama        | character varying(100)      |           | not null | 
 tipe        | character varying(20)       |           |          | 
 created_at  | timestamp without time zone |           | not null | now()
 updated_at  | timestamp without time zone |           | not null | now()
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
      Column       |            Type             | Collation | Nullable |                Default                
-------------------+-----------------------------+-----------+----------+---------------------------------------
 id                | integer                     |           | not null | nextval('kecamatan_id_seq'::regclass)
 kabupaten_kota_id | integer                     |           |          | 
 kode              | character varying(10)       |           | not null | 
 nama              | character varying(100)      |           | not null | 
 created_at        | timestamp without time zone |           | not null | now()
 updated_at        | timestamp without time zone |           | not null | now()
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
        Column        |            Type             | Collation | Nullable |                   Default                    
----------------------+-----------------------------+-----------+----------+----------------------------------------------
 id                   | integer                     |           | not null | nextval('koleksi_tumbuhan_id_seq'::regclass)
 nomor_koleksi        | character varying(100)      |           |          | 
 nama_lokal_daerah    | character varying(255)      |           |          | 
 nama_umum_nasional   | character varying(255)      |           |          | 
 nama_ilmiah          | character varying(255)      |           | not null | 
 genus                | character varying(100)      |           |          | 
 spesies              | character varying(100)      |           |          | 
 author               | character varying(255)      |           |          | 
 sumber_publikasi     | text                        |           |          | 
 bentuk_pohon         | text                        |           |          | 
 bentuk_daun          | text                        |           |          | 
 bentuk_bunga         | text                        |           |          | 
 bentuk_buah          | text                        |           |          | 
 waktu_berbunga       | character varying(100)      |           |          | 
 waktu_berbuah        | character varying(100)      |           |          | 
 taman_kehati_id      | integer                     |           | not null | 
 zona_id              | integer                     |           |          | 
 latitude_taman       | numeric(10,8)               |           |          | 
 longitude_taman      | numeric(11,8)               |           |          | 
 koordinat_taman      | geometry(Point,4326)        |           |          | 
 ketinggian_taman     | integer                     |           |          | 
 asal_kampung         | character varying(100)      |           |          | 
 asal_desa_id         | integer                     |           |          | 
 asal_kecamatan_id    | integer                     |           |          | 
 asal_kabupaten_id    | integer                     |           |          | 
 asal_provinsi_id     | integer                     |           |          | 
 latitude_asal        | numeric(10,8)               |           |          | 
 longitude_asal       | numeric(11,8)               |           |          | 
 koordinat_asal       | geometry(Point,4326)        |           |          | 
 ketinggian_asal      | integer                     |           |          | 
 sebaran_global       | text                        |           |          | 
 referensi_sebaran    | text                        |           |          | 
 status_endemik       | status_endemik              |           |          | 'tidak_diketahui'::status_endemik
 habitat_alami        | text                        |           |          | 
 referensi_habitat    | text                        |           |          | 
 metode_perbanyakan   | text                        |           |          | 
 manfaat_masyarakat   | text                        |           |          | 
 manfaat_lingkungan   | text                        |           |          | 
 potensi_pengembangan | text                        |           |          | 
 tanggal_pengumpulan  | date                        |           |          | 
 tanggal_penanaman    | date                        |           |          | 
 status               | status_publikasi            |           | not null | 'draft'::status_publikasi
 created_by           | uuid                        |           |          | 
 updated_by           | uuid                        |           |          | 
 created_at           | timestamp without time zone |           | not null | now()
 updated_at           | timestamp without time zone |           | not null | now()
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
       Column        |            Type             | Collation | Nullable |              Default              
---------------------+-----------------------------+-----------+----------+-----------------------------------
 id                  | integer                     |           | not null | nextval('media_id_seq'::regclass)
 taman_kehati_id     | integer                     |           |          | 
 koleksi_tumbuhan_id | integer                     |           |          | 
 media_type          | media_type                  |           | not null | 
 media_category      | media_category              |           | not null | 
 file_name           | character varying(255)      |           | not null | 
 file_path           | character varying(500)      |           | not null | 
 file_size           | integer                     |           |          | 
 mime_type           | character varying(100)      |           |          | 
 caption             | text                        |           |          | 
 is_main_image       | boolean                     |           |          | false
 uploaded_by         | uuid                        |           |          | 
 created_at          | timestamp without time zone |           | not null | now()
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
       Column        |            Type             | Collation | Nullable |                Default                 
---------------------+-----------------------------+-----------+----------+----------------------------------------
 id                  | integer                     |           | not null | nextval('page_views_id_seq'::regclass)
 taman_kehati_id     | integer                     |           |          | 
 koleksi_tumbuhan_id | integer                     |           |          | 
 page_type           | character varying(50)       |           | not null | 
 ip_address          | character varying(45)       |           |          | 
 user_agent          | text                        |           |          | 
 referrer            | text                        |           |          | 
 session_id          | character varying(100)      |           |          | 
 created_at          | timestamp without time zone |           | not null | now()
Indexes:
    "page_views_pkey" PRIMARY KEY, btree (id)
    "views_date_idx" btree (created_at)
    "views_koleksi_idx" btree (koleksi_tumbuhan_id)
    "views_taman_idx" btree (taman_kehati_id)
Foreign-key constraints:
    "page_views_koleksi_tumbuhan_id_koleksi_tumbuhan_id_fk" FOREIGN KEY (koleksi_tumbuhan_id) REFERENCES koleksi_tumbuhan(id)
    "page_views_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)

                                        Table "public.provinsi"
   Column   |            Type             | Collation | Nullable |               Default                
------------+-----------------------------+-----------+----------+--------------------------------------
 id         | integer                     |           | not null | nextval('provinsi_id_seq'::regclass)
 kode       | character varying(10)       |           | not null | 
 nama       | character varying(100)      |           | not null | 
 pulau      | character varying(50)       |           |          | 
 created_at | timestamp without time zone |           | not null | now()
 updated_at | timestamp without time zone |           | not null | now()
Indexes:
    "provinsi_pkey" PRIMARY KEY, btree (id)
    "provinsi_kode_unique" UNIQUE CONSTRAINT, btree (kode)
Referenced by:
    TABLE "kabupaten_kota" CONSTRAINT "kabupaten_kota_provinsi_id_provinsi_id_fk" FOREIGN KEY (provinsi_id) REFERENCES provinsi(id)
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_asal_provinsi_id_provinsi_id_fk" FOREIGN KEY (asal_provinsi_id) REFERENCES provinsi(id)
    TABLE "taman_kehati" CONSTRAINT "taman_kehati_provinsi_id_provinsi_id_fk" FOREIGN KEY (provinsi_id) REFERENCES provinsi(id)

                                             Table "public.search_index"
       Column        |            Type             | Collation | Nullable |                 Default                  
---------------------+-----------------------------+-----------+----------+------------------------------------------
 id                  | integer                     |           | not null | nextval('search_index_id_seq'::regclass)
 taman_kehati_id     | integer                     |           |          | 
 koleksi_tumbuhan_id | integer                     |           |          | 
 searchable_text     | text                        |           | not null | 
 entity_type         | character varying(20)       |           | not null | 
 updated_at          | timestamp without time zone |           | not null | now()
Indexes:
    "search_index_pkey" PRIMARY KEY, btree (id)
    "search_fulltext_idx" gin (to_tsvector('indonesian'::regconfig, searchable_text))
    "search_koleksi_idx" btree (koleksi_tumbuhan_id)
    "search_taman_idx" btree (taman_kehati_id)
Foreign-key constraints:
    "search_index_koleksi_tumbuhan_id_koleksi_tumbuhan_id_fk" FOREIGN KEY (koleksi_tumbuhan_id) REFERENCES koleksi_tumbuhan(id)
    "search_index_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)

                    Table "public.spatial_ref_sys"
  Column   |          Type           | Collation | Nullable | Default 
-----------+-------------------------+-----------+----------+---------
 srid      | integer                 |           | not null | 
 auth_name | character varying(256)  |           |          | 
 auth_srid | integer                 |           |          | 
 srtext    | character varying(2048) |           |          | 
 proj4text | character varying(2048) |           |          | 
Indexes:
    "spatial_ref_sys_pkey" PRIMARY KEY, btree (srid)
Check constraints:
    "spatial_ref_sys_srid_check" CHECK (srid > 0 AND srid <= 998999)

                                            Table "public.taman_kehati"
      Column       |            Type             | Collation | Nullable |                 Default                  
-------------------+-----------------------------+-----------+----------+------------------------------------------
 id                | integer                     |           | not null | nextval('taman_kehati_id_seq'::regclass)
 kode              | character varying(50)       |           |          | 
 nama_resmi        | character varying(255)      |           | not null | 
 alamat            | text                        |           | not null | 
 luas              | numeric(10,2)               |           |          | 
 tipe_taman        | tipe_taman                  |           | not null | 
 tanggal_penetapan | date                        |           |          | 
 deskripsi         | text                        |           |          | 
 provinsi_id       | integer                     |           | not null | 
 kabupaten_kota_id | integer                     |           | not null | 
 kecamatan_id      | integer                     |           |          | 
 desa_id           | integer                     |           |          | 
 latitude          | numeric(10,8)               |           |          | 
 longitude         | numeric(11,8)               |           |          | 
 koordinat         | geometry(Point,4326)        |           |          | 
 batas_area        | geometry(Polygon,4326)      |           |          | 
 status            | status_publikasi            |           | not null | 'draft'::status_publikasi
 created_by        | uuid                        |           |          | 
 updated_by        | uuid                        |           |          | 
 created_at        | timestamp without time zone |           | not null | now()
 updated_at        | timestamp without time zone |           | not null | now()
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
     Column      |            Type             | Collation | Nullable |       Default       
-----------------+-----------------------------+-----------+----------+---------------------
 id              | uuid                        |           | not null | gen_random_uuid()
 email           | character varying(255)      |           | not null | 
 password        | character varying(255)      |           | not null | 
 nama            | character varying(255)      |           | not null | 
 role            | user_role                   |           | not null | 'viewer'::user_role
 is_active       | boolean                     |           | not null | true
 taman_kehati_id | integer                     |           |          | 
 created_at      | timestamp without time zone |           | not null | now()
 updated_at      | timestamp without time zone |           | not null | now()
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
     Column      |            Type             | Collation | Nullable |                Default                 
-----------------+-----------------------------+-----------+----------+----------------------------------------
 id              | integer                     |           | not null | nextval('zona_taman_id_seq'::regclass)
 taman_kehati_id | integer                     |           | not null | 
 kode_zona       | character varying(50)       |           | not null | 
 nama_zona       | character varying(100)      |           |          | 
 deskripsi       | text                        |           |          | 
 luas            | numeric(10,2)               |           |          | 
 poligon         | geometry(Polygon,4326)      |           |          | 
 warna           | character varying(7)        |           |          | 
 created_at      | timestamp without time zone |           | not null | now()
 updated_at      | timestamp without time zone |           | not null | now()
Indexes:
    "zona_taman_pkey" PRIMARY KEY, btree (id)
    "taman_zona_unique" UNIQUE CONSTRAINT, btree (taman_kehati_id, kode_zona)
    "zona_poligon_idx" gist (poligon)
Foreign-key constraints:
    "zona_taman_taman_kehati_id_taman_kehati_id_fk" FOREIGN KEY (taman_kehati_id) REFERENCES taman_kehati(id)
Referenced by:
    TABLE "koleksi_tumbuhan" CONSTRAINT "koleksi_tumbuhan_zona_id_zona_taman_id_fk" FOREIGN KEY (zona_id) REFERENCES zona_taman(id)

postgres=> \dt
                 List of relations
 Schema |       Name       | Type  |     Owner      
--------+------------------+-------+----------------
 public | artikel          | table | postgres
 public | audit_log        | table | postgres
 public | desa             | table | postgres
 public | kabupaten_kota   | table | postgres
 public | kecamatan        | table | postgres
 public | koleksi_tumbuhan | table | postgres
 public | media            | table | postgres
 public | page_views       | table | postgres
 public | provinsi         | table | postgres
 public | search_index     | table | postgres
 public | spatial_ref_sys  | table | supabase_admin
 public | taman_kehati     | table | postgres
 public | users            | table | postgres
 public | zona_taman       | table | postgres
(14 rows)

postgres=> 
