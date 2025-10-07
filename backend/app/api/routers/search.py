from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.search import SearchBase, SearchResponse, SearchResult, SuggestBase, SuggestResponse
from app.auth.utils import get_current_active_user, get_current_super_admin
from app.utils.logging_config import get_logger
from sqlalchemy import text
from app.models import TamanKehati, KoleksiTumbuhan, Artikel, SearchIndex
from sqlalchemy.orm import selectinload

router = APIRouter()
logger = get_logger(__name__)

@router.get("/", response_model=SearchResponse,
             summary="Full-text search",
             description="Search across entities with Indonesian tokenizer",
             responses={
                 200: {
                     "description": "Search results",
                     "content": {
                         "application/json": {
                             "example": {
                                 "query": "bambu",
                                 "entity": "all",
                                 "total": 2,
                                 "results": [
                                     {
                                         "id": 1,
                                         "entity_type": "koleksi",
                                         "title": "Bambusa oldhamii",
                                         "snippet": "Bambusa oldhamii adalah jenis bambu yang tumbuh tinggi...",
                                         "score": 0.95
                                     },
                                     {
                                         "id": 5,
                                         "entity_type": "taman",
                                         "title": "Taman Wisata Alam Bambu",
                                         "snippet": "TWA Bambu adalah kawasan konservasi yang menyimpan berbagai jenis bambu...",
                                         "score": 0.87
                                     }
                                 ]
                             }
                         }
                     }
                 }
             })
async def search_entities(
    q: str,
    entity: str = "all",  # "all", "taman", "koleksi", "artikel"
    limit: int = 20,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Full-text search across entities with Indonesian tokenizer"""
    logger.info(f"Search request - query: '{q}', entity: {entity}, limit: {limit}, user: {current_user.email}")
    
    if len(q) < 2:
        return SearchResponse(query=q, entity=entity, total=0, results=[])
    
    results = []
    
    # Search using FTS with Indonesian configuration
    if entity in ["all", "taman"]:
        # Search in taman_kehati table
        taman_query = text("""
            SELECT 
                taman_kehati.id,
                nama_resmi as title,
                alamat as snippet,
                ts_rank(to_tsvector('indonesian', searchable_text), websearch_to_tsquery('indonesian', :query)) as score
            FROM taman_kehati
            JOIN search_index ON taman_kehati.id = search_index.taman_kehati_id
            WHERE to_tsvector('indonesian', searchable_text) @@ websearch_to_tsquery('indonesian', :query)
            AND status = 'published'
            ORDER BY score DESC
            LIMIT :limit
        """)
        
        taman_result = await db.execute(
            taman_query,
            {"query": q, "limit": limit}
        )
        
        for row in taman_result:
            results.append(SearchResult(
                id=row.id,
                entity_type="taman",
                title=row.title,
                snippet=row.snippet[:100] + "..." if len(row.snippet) > 100 else row.snippet,
                score=float(row.score)
            ))
    
    if entity in ["all", "koleksi"]:
        # Search in koleksi_tumbuhan table
        koleksi_query = text("""
            SELECT 
                koleksi_tumbuhan.id,
                nama_ilmiah as title,
                COALESCE(bentuk_pohon, '') || ' ' || COALESCE(bentuk_daun, '') as snippet,
                ts_rank(to_tsvector('indonesian', searchable_text), websearch_to_tsquery('indonesian', :query)) as score
            FROM koleksi_tumbuhan
            JOIN search_index ON koleksi_tumbuhan.id = search_index.koleksi_tumbuhan_id
            WHERE to_tsvector('indonesian', searchable_text) @@ websearch_to_tsquery('indonesian', :query)
            AND status = 'published'
            ORDER BY score DESC
            LIMIT :limit
        """)
        
        koleksi_result = await db.execute(
            koleksi_query,
            {"query": q, "limit": limit}
        )
        
        for row in koleksi_result:
            results.append(SearchResult(
                id=row.id,
                entity_type="koleksi",
                title=row.title,
                snippet=row.snippet[:100] + "..." if len(row.snippet) > 100 else row.snippet,
                score=float(row.score)
            ))
    
    # Sort all results by score and limit to specified number
    results.sort(key=lambda x: x.score, reverse=True)
    results = results[:limit]
    
    response = SearchResponse(
        query=q,
        entity=entity,
        total=len(results),
        results=results
    )
    
    logger.info(f"Search completed successfully, returned {len(results)} results")
    return response


@router.get("/suggest", response_model=SuggestResponse)
async def search_suggest(
    q: str,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get search suggestions"""
    logger.info(f"Search suggestions request - query: '{q}', user: {current_user.email}")
    
    if len(q) < 2:
        return SuggestResponse(suggestions=[])
    
    suggestions = []
    
    # Get suggestions from taman_kehati names
    taman_query = text("""
        SELECT DISTINCT nama_resmi
        FROM taman_kehati
        WHERE to_tsvector('indonesian', nama_resmi) @@ plainto_tsquery('indonesian', :query)
        LIMIT 5
    """)
    
    taman_result = await db.execute(taman_query, {"query": q})
    for row in taman_result:
        suggestions.append(row[0])
    
    # Get suggestions from koleksi names
    koleksi_query = text("""
        SELECT DISTINCT nama_ilmiah
        FROM koleksi_tumbuhan
        WHERE to_tsvector('indonesian', nama_ilmiah) @@ plainto_tsquery('indonesian', :query)
        LIMIT 5
    """)
    
    koleksi_result = await db.execute(koleksi_query, {"query": q})
    for row in koleksi_result:
        suggestions.append(row[0])
    
    # Remove duplicates while preserving order
    unique_suggestions = list(dict.fromkeys(suggestions))[:10]
    
    logger.info(f"Search suggestions completed, returned {len(unique_suggestions)} suggestions")
    return SuggestResponse(suggestions=unique_suggestions)


@router.post("/reindex", response_model=dict)
async def reindex_search(
    current_user=Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Rebuild search index (super_admin only)"""
    logger.info(f"Reindexing search started by super_admin: {current_user.email}")
    
    try:
        # Clear existing search index
        await db.execute(text("DELETE FROM search_index"))
        
        # Rebuild from taman_kehati
        taman_result = await db.execute(text("""
            INSERT INTO search_index (taman_kehati_id, searchable_text, entity_type, updated_at)
            SELECT 
                id,
                CONCAT_WS(' ', COALESCE(nama_resmi, ''), COALESCE(alamat, ''), COALESCE(deskripsi, '')) as searchable_text,
                'taman' as entity_type,
                updated_at
            FROM taman_kehati
        """))
        
        # Rebuild from koleksi_tumbuhan
        koleksi_result = await db.execute(text("""
            INSERT INTO search_index (koleksi_tumbuhan_id, searchable_text, entity_type, updated_at)
            SELECT 
                id,
                CONCAT_WS(' ', 
                    COALESCE(nama_ilmiah, ''), 
                    COALESCE(nama_umum_nasional, ''), 
                    COALESCE(nama_lokal_daerah, ''),
                    COALESCE(bentuk_pohon, ''),
                    COALESCE(bentuk_daun, ''),
                    COALESCE(bentuk_bunga, ''),
                    COALESCE(bentuk_buah, '')
                ) as searchable_text,
                'koleksi' as entity_type,
                updated_at
            FROM koleksi_tumbuhan
        """))
        
        await db.commit()
        
        logger.info("Search index rebuilt successfully")
        return {"message": "Search index rebuilt successfully", "status": "completed"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Search reindex failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindex failed: {str(e)}"
        )