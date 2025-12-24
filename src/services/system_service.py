import asyncio
from sqlmodel import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from src.models import User, Location, AccessLog
from src.schemas import SystemCountersResponse


class SystemService:
    """Service class for system stats operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_system_counters(self) -> SystemCountersResponse:
        """Get System Counters"""

        # User Counts by Role and Plan
        stmt_users = select(
            func.count().filter(User.role == 'ADMIN').label('count_admin'),
            func.count().filter(User.role == 'JANITOR').label('count_janitor'),
            func.count().filter(User.plan_id == 1).label('count_demo')
        )
        res_users_raw = await self.session.execute(stmt_users)
        res_users = res_users_raw.first()

        # Location Counts
        stmt_locations = select(func.count(Location.id))
        res_locations = await self.session.scalar(stmt_locations)

        # Access Logs Today
        stmt_access = select(func.count(AccessLog.id)).where(
            func.date(AccessLog.created_at) == date.today()
        )
        res_access = await self.session.scalar(stmt_access)

        return {
            "users_admin": res_users.count_admin or 0,
            "users_janitors": res_users.count_janitor or 0,
            "users_plan_demo": res_users.count_demo or 0,
            "total_entrances": res_locations or 0,
            "income_today": res_access or 0
        }
