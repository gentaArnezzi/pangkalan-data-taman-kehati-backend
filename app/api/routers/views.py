from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas.views import ViewTrackCreate, ViewSeriesQuery, ViewSeriesResponse, ViewSeriesDataPoint, TopViewsQuery, TopViewsResponse, TopView
from app.auth.utils import get_current_active_user, get_current_admin
from app.utils.logging_config import get_logger
from sqlalchemy import text, select, func, and_, or_
from app.models import PageViews, TamanKehati, KoleksiTumbuhan, Artikel
import json

router = APIRouter()
logger = get_logger(__name__)

@router.post("/track", response_model=dict,
             summary="Track page view",
             description="Track page views (public endpoint - no auth required)",
             responses={
                 200: {
                     "description": "View tracked successfully",
                     "content": {
                         "application/json": {
                             "example": {
                                 "message": "View tracked successfully",
                                 "status": "success"
                             }
                         }
                     }
                 }
             })
async def track_view(
    view_track: ViewTrackCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Track page views (public endpoint - no auth required)
    This endpoint does not require authentication to allow tracking from public pages
    """
    logger.info(f"Tracking view - page_type: {view_track.page_type}, entity: taman={view_track.taman_kehati_id}, koleksi={view_track.koleksi_tumbuhan_id}")
    
    # Validate that at least one entity ID is provided
    if not view_track.taman_kehati_id and not view_track.koleksi_tumbuhan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either taman_kehati_id or koleksi_tumbuhan_id must be provided"
        )
    
    # Create page view record
    from app.models import PageViews as PageViewsModel
    from uuid import uuid4
    
    page_view = PageViewsModel(
        taman_kehati_id=view_track.taman_kehati_id,
        koleksi_tumbuhan_id=view_track.koleksi_tumbuhan_id,
        page_type=view_track.page_type,
        ip_address=view_track.ip_address,
        user_agent=view_track.user_agent,
        referrer=view_track.referrer,
        session_id=view_track.session_id
    )
    
    db.add(page_view)
    await db.commit()
    
    logger.info(f"Successfully tracked view for page_type: {view_track.page_type}")
    return {"message": "View tracked successfully", "status": "success"}


@router.get("/series", response_model=ViewSeriesResponse)
async def get_view_series(
    entity: str,  # 'taman', 'koleksi', 'artikel'
    id: int,
    range: str = "7d",  # '7d', '30d', 'custom'
    interval: str = "day",  # 'day', 'week', 'month'
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get view series data for analytics"""
    logger.info(f"Getting view series - entity: {entity}, id: {id}, range: {range}, interval: {interval}, user: {current_user.email}")
    
    # Validate entity parameter
    valid_entities = ["taman", "koleksi", "artikel"]
    if entity not in valid_entities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity: {entity}. Valid options: {valid_entities}"
        )
    
    # Determine date range
    end_date = datetime.utcnow()
    if range == "7d":
        start_date = end_date - timedelta(days=7)
    elif range == "30d":
        start_date = end_date - timedelta(days=30)
    else:
        # For custom range, we'll use the last 7 days as default
        start_date = end_date - timedelta(days=7)
    
    # Build query based on entity
    date_trunc_expr = f"DATE_TRUNC('{interval}', created_at)"
    
    base_query = text(f"""
        SELECT 
            {date_trunc_expr} as date,
            COUNT(*) as count
        FROM page_views
        WHERE 
            created_at >= :start_date 
            AND created_at <= :end_date
    """)
    
    params = {"start_date": start_date, "end_date": end_date}
    
    if entity == "taman":
        base_query = text(f"""
            SELECT 
                {date_trunc_expr} as date,
                COUNT(*) as count
            FROM page_views
            WHERE 
                taman_kehati_id = :entity_id
                AND created_at >= :start_date 
                AND created_at <= :end_date
            GROUP BY {date_trunc_expr}
            ORDER BY {date_trunc_expr}
        """)
        params["entity_id"] = id
    elif entity == "koleksi":
        base_query = text(f"""
            SELECT 
                {date_trunc_expr} as date,
                COUNT(*) as count
            FROM page_views
            WHERE 
                koleksi_tumbuhan_id = :entity_id
                AND created_at >= :start_date 
                AND created_at <= :end_date
            GROUP BY {date_trunc_expr}
            ORDER BY {date_trunc_expr}
        """)
        params["entity_id"] = id
    elif entity == "artikel":
        # For artikel, we might need to join with artikel table if needed
        # For now, we'll just query page views with a specific page type
        base_query = text(f"""
            SELECT 
                {date_trunc_expr} as date,
                COUNT(*) as count
            FROM page_views
            WHERE 
                page_type = :page_type
                AND created_at >= :start_date 
                AND created_at <= :end_date
            GROUP BY {date_trunc_expr}
            ORDER BY {date_trunc_expr}
        """)
        params["page_type"] = f"artikel-{id}"
    
    result = await db.execute(base_query, params)
    rows = result.fetchall()
    
    # Convert to response format
    data_points = []
    total = 0
    
    for row in rows:
        data_points.append(ViewSeriesDataPoint(
            date=row.date.isoformat() if hasattr(row.date, 'isoformat') else str(row.date),
            count=row.count
        ))
        total += row.count
    
    response = ViewSeriesResponse(data=data_points, total=total)
    logger.info(f"Successfully returned view series with {len(data_points)} data points")
    return response


@router.get("/top", response_model=TopViewsResponse)
async def get_top_views(
    entity: str,  # 'koleksi', 'artikel' 
    taman_kehati_id: int = None,
    range: str = "7d",  # '7d', '30d'
    limit: int = 10,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get top viewed items"""
    logger.info(f"Getting top views - entity: {entity}, taman_kehati_id: {taman_kehati_id}, range: {range}, limit: {limit}, user: {current_user.email}")
    
    # Validate entity parameter
    valid_entities = ["koleksi", "artikel"]
    if entity not in valid_entities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entity: {entity}. Valid options: {valid_entities}"
        )
    
    # Determine date range
    end_date = datetime.utcnow()
    if range == "7d":
        start_date = end_date - timedelta(days=7)
    elif range == "30d":
        start_date = end_date - timedelta(days=30)
    else:
        # Default to 7 days
        start_date = end_date - timedelta(days=7)
    
    results = []
    
    if entity == "koleksi":
        # Query top collections
        query = text(f"""
            SELECT 
                koleksi_tumbuhan_id as id,
                COUNT(*) as view_count
            FROM page_views
            WHERE 
                koleksi_tumbuhan_id IS NOT NULL
                AND created_at >= :start_date 
                AND created_at <= :end_date
        """)
        
        params = {"start_date": start_date, "end_date": end_date}
        
        if taman_kehati_id:
            query = text(f"""
                SELECT 
                    pv.koleksi_tumbuhan_id as id,
                    COUNT(*) as view_count
                FROM page_views pv
                JOIN koleksi_tumbuhan kt ON pv.koleksi_tumbuhan_id = kt.id
                WHERE 
                    pv.koleksi_tumbuhan_id IS NOT NULL
                    AND kt.taman_kehati_id = :taman_id
                    AND pv.created_at >= :start_date 
                    AND pv.created_at <= :end_date
                GROUP BY pv.koleksi_tumbuhan_id
                ORDER BY view_count DESC
                LIMIT :limit
            """)
            params["taman_id"] = taman_kehati_id
            params["limit"] = limit
        else:
            query = text(f"""
                SELECT 
                    koleksi_tumbuhan_id as id,
                    COUNT(*) as view_count
                FROM page_views
                WHERE 
                    koleksi_tumbuhan_id IS NOT NULL
                    AND created_at >= :start_date 
                    AND created_at <= :end_date
                GROUP BY koleksi_tumbuhan_id
                ORDER BY view_count DESC
                LIMIT :limit
            """)
            params["limit"] = limit
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        # Get titles for the top collections
        if rows:
            ids = [row.id for row in rows]
            koleksi_result = await db.execute(
                select(KoleksiTumbuhan.id, KoleksiTumbuhan.nama_ilmiah)
                .filter(KoleksiTumbuhan.id.in_(ids))
            )
            koleksi_titles = {k.id: k.nama_ilmiah for k in koleksi_result}
        
        for row in rows:
            title = koleksi_titles.get(row.id, f"Koleksi #{row.id}")
            results.append(TopView(
                id=row.id,
                title=title,
                view_count=row.view_count,
                entity_type="koleksi"
            ))
    
    response = TopViewsResponse(results=results)
    logger.info(f"Successfully returned top {len(results)} viewed {entity} items")
    return response