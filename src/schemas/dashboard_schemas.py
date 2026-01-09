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
    month: int
    count: int


class KpisResponse(BaseModel):
    historical_total: int
    entries_today: int
    currently_inside: int
    whitelist: KpisWhitelistResponse
    blacklist: KpisBlacklistResponse


class GenderSchema(BaseModel):
    male: int
    female: int


class RecentEntriesSchema(BaseModel):
    name: str
    identifier: str
    destination: str
    timestamp: datetime


class MonthlyIncomeResponse(BaseModel):  # FOR TESTING PURPOSES ONLY
    entries_by_month: List[IndividualMonthSchema]


class RecentEntriesResponse(BaseModel):  # FOR TESTING PURPOSES ONLY
    recent_entries: List[RecentEntriesSchema]


__all__ = [
    "KpisResponse",
    "KpisWhitelistResponse",
    "KpisBlacklistResponse",
]
