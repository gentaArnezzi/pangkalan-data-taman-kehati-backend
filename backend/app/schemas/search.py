from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum


class SearchEntityEnum(str, Enum):
    all = "all"
    artikel = "artikel"
    koleksi = "koleksi"
    taman = "taman"


class SearchBase(BaseModel):
    q: str
    entity: Optional[SearchEntityEnum] = None
    limit: Optional[int] = 20


class SearchResult(BaseModel):
    id: int
    entity_type: str
    title: str
    snippet: str
    score: float


class SearchResponse(BaseModel):
    query: str
    entity: Optional[SearchEntityEnum]
    total: int
    results: List[SearchResult]


class SuggestBase(BaseModel):
    q: str


class SuggestResponse(BaseModel):
    suggestions: List[str]