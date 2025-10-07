from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .api.routers import taman_kehati, koleksi_tumbuhan, users, auth, data_export
from .api.routers import provinsi as geo_ref
from .api.routers import zona_taman as zona
from .api.routers import media
from .api.routers import search
from .api.routers import views
from .api.routers import audit
from .api.routers import meta
from .api.routers import artikel
from .utils.logging_config import get_logger
import os
from .database import engine
from sqlalchemy import text

# Setup logging for main application
logger = get_logger(__name__)

app = FastAPI(
    title="Taman Kehati API",
    description="API for Taman Keanekaragaman Hayati (Kehati) Indonesia Data Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



logger.info("Taman Kehati API application initialized")

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(taman_kehati.router, prefix="/api/taman", tags=["taman"])
app.include_router(koleksi_tumbuhan.router, prefix="/api/koleksi", tags=["koleksi"])
app.include_router(geo_ref.router, prefix="/api", tags=["geography"])
app.include_router(zona.router, prefix="/api/zona", tags=["zona"])
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(artikel.router, prefix="/api/artikel", tags=["artikel"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(views.router, prefix="/api/views", tags=["views"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(meta.router, prefix="/api/meta", tags=["meta"])
app.include_router(data_export.router, prefix="/api", tags=["data-export"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Taman Kehati API"}

@app.get("/health")
async def health_check():
    """Health check endpoint that validates DB connection, PostGIS availability, and FTS readiness"""
    try:
        async with engine.connect() as conn:
            # Test basic connection
            db_status = await conn.scalar(text("select 1"))
            
            # Test PostGIS availability
            postgis_status = await conn.scalar(text("SELECT PostGIS_version()"))
            
            # Test FTS (Full Text Search) availability
            fts_status = await conn.scalar(text("SELECT to_tsvector('indonesian', 'test')"))
            
            return {
                "status": "healthy",
                "checks": {
                    "database": "ok" if db_status == 1 else "failed",
                    "postgis": "ok" if postgis_status else "failed",
                    "fts_indonesian": "ok" if fts_status is not None else "failed"
                }
            }
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@app.on_event("startup")
async def _db_ping():
    try:
        async with engine.connect() as conn:
            # Test basic connection
            try:
                val = await conn.scalar(text("select 1"))
                logger.info("DB ping OK: %s", val)
            except Exception as e:
                logger.error("DB basic connection failed: %s", str(e))
                raise

            # Test PostGIS availability
            try:
                postgis_version = await conn.scalar(text("SELECT PostGIS_version()"))
                logger.info("PostGIS available: %s", postgis_version)
            except Exception as e:
                logger.error("PostGIS check failed: %s", str(e))
                logger.error("Please ensure the PostGIS extension is installed and enabled in your database.")
                raise

            # Test FTS (Full Text Search) availability
            try:
                fts_test = await conn.scalar(text("SELECT to_tsvector('indonesian', 'test')"))
                logger.info("FTS (Indonesian) available: %s", fts_test is not None)
            except Exception as e:
                logger.error("FTS (Indonesian) check failed: %s", str(e))
                logger.error("Please ensure the 'indonesian' FTS dictionary is installed in your database.")
                raise

    except Exception as e:
        logger.error("DB ping failed: %s", str(e))
        raise