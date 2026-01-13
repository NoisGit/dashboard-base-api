"""Stats schema definitions."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class KpisWhitelistResponse(BaseModel):
    today: int
    total: int


class KpisBlacklistResponse(BaseModel):
    total: int


class IndividualMonthSchema(BaseModel):
    month: str
    count: int


class KpisResponse(BaseModel):
    historical_total: int
    entries_today: int
    currently_inside: int
    whitelist: KpisWhitelistResponse
    blacklist: KpisBlacklistResponse


class GenderDistributionResponse(BaseModel):
    male: float
    female: float


class RecentEntriesSchema(BaseModel):
    name: str
    identifier: str
    destination: str
    timestamp: datetime


class EntriesByMonthResponse(BaseModel):  # FOR TESTING PURPOSES ONLY
    entries_by_month: List[IndividualMonthSchema]


class RecentEntriesResponse(BaseModel):  # FOR TESTING PURPOSES ONLY
    recent_entries: List[RecentEntriesSchema]


class ChartStatsResponse(BaseModel):
    gender_distribution: GenderDistributionResponse
    entries_by_month: EntriesByMonthResponse


class DashboardStatsResponse(BaseModel):
    kpis: KpisResponse
    charts: ChartStatsResponse
    recent_entries: List[RecentEntriesSchema]


__all__ = [
    "KpisResponse",
    "KpisWhitelistResponse",
    "KpisBlacklistResponse",
    "EntriesByMonthResponse",
    "DashboardStatsResponse",
    "GenderDistributionResponse",
    "ChartStatsResponse",
    "RecentEntriesResponse",
]
