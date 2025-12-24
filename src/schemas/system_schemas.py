"""Stats schema definitions."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class SystemCountersResponse(BaseModel):
    users_admin: int
    users_janitors: int
    users_plan_demo: int
    total_entrances: int
    income_today: int


class MonthlyIncomeResponse(BaseModel):
    year: int
    month: int
    quantity: int


class AdminDetailResponse(BaseModel):
    id_user: int
    name: str
    email: EmailStr
    logo: Optional[str]
    plan: Optional[str]
    creation_date: datetime
    entrances_count: int
    janitors_count: int


class StatsDataResponse(BaseModel):
    counters: SystemCountersResponse
    detail_income_by_month: List[MonthlyIncomeResponse]
    detail_admins: List[AdminDetailResponse]


class SystemStatsResponse(BaseModel):
    status: str
    message: str
    data: StatsDataResponse


__all__ = [
    "SystemCountersResponse",
    "MonthlyIncomeResponse",
    "AdminDetailResponse",
    "StatsDataResponse",
    "SystemStatsResponse",
]
