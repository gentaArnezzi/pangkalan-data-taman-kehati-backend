from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ViewTrackBase(BaseModel):
    page_type: str
    taman_kehati_id: Optional[int] = None
    koleksi_tumbuhan_id: Optional[int] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None


class ViewTrackCreate(ViewTrackBase):
    pass


class ViewSeriesRangeEnum(str, Enum):
    d7 = "7d"
    d30 = "30d"
    custom = "custom"


class ViewSeriesIntervalEnum(str, Enum):
    day = "day"
    week = "week"
    month = "month"


class ViewSeriesQuery(BaseModel):
    entity: str  # 'taman', 'koleksi', 'artikel'
    id: int
    range: ViewSeriesRangeEnum = ViewSeriesRangeEnum.d7
    interval: ViewSeriesIntervalEnum = ViewSeriesIntervalEnum.day
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class ViewSeriesDataPoint(BaseModel):
    date: str
    count: int


class ViewSeriesResponse(BaseModel):
    data: List[ViewSeriesDataPoint]
    total: int


class TopViewsQuery(BaseModel):
    entity: str  # 'artikel', 'koleksi'
    taman_kehati_id: Optional[int] = None
    range: str = "7d"
    limit: int = 10


class TopView(BaseModel):
    id: int
    title: str
    view_count: int
    entity_type: str


class TopViewsResponse(BaseModel):
    results: List[TopView]