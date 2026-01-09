from datetime import date
from sqlmodel import select
from sqlalchemy import func, desc, and_, cast, Date
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.enums import UserRole
from src.services import UserService

from src.models import AccessLog, AccessList, TypeAccessList, Location

from sqlalchemy.orm import aliased
from src.schemas import (
    KpisResponse,
    KpisBlacklistResponse,
    KpisWhitelistResponse
)


class DashboardService:
    """Service class for system stats operations"""

    def __init__(
        self,
        session: AsyncSession,
        user_service: UserService,
    ):
        self.session = session
        self.user_service = user_service

    async def get_type_list(self, name_list: str) -> TypeAccessList:
        """Get data from type list"""

        stmt_type_list = select(TypeAccessList).where(
            TypeAccessList.name == name_list)
        result_type_list = await self.session.execute(stmt_type_list)
        type_list = result_type_list.scalars().first()

        return type_list

    async def get_kpis_whitelist(self, location_id: int) -> KpisWhitelistResponse:
        """Get Whitelist KPIs Counters"""

        # Get Id list type
        type_list = await self.get_type_list("whitelist")

        #  Whitelist Counts
        stmt_access_whitelist = select(
            func.count(AccessList.id).label('whitelist_total')
        ).where(AccessList.location_id == location_id, AccessList.type_access_list_id == type_list.id)
        res_access_whitelist_counts_raw = await self.session.execute(stmt_access_whitelist)
        res__access_whitelist_counts = res_access_whitelist_counts_raw.first()

        # Whitelist Today's Count (Placeholder logic, adjust as needed)
        stmt_whitelist_today = (
            select(
                func.count().filter(cast(AccessLog.created_at, Date)
                                    == date.today()).label('whitelist_today'),
            )
            .outerjoin(AccessList, AccessLog.external_people_id == AccessList.external_people_id)
            .where(AccessLog.location_id == location_id, AccessList.location_id == location_id, AccessList.type_access_list_id == type_list.id)
        )

        res_access_whitelist_today_raw = await self.session.execute(stmt_whitelist_today)
        res__access_whitelist_today = res_access_whitelist_today_raw.first()

        return KpisWhitelistResponse(
            total=res__access_whitelist_counts.whitelist_total,
            today=res__access_whitelist_today.whitelist_today
        )

    async def get_kpis_blacklist(self, location_id: int) -> KpisBlacklistResponse:
        """Get Blacklist KPIs Counters"""

        # Get Id list type
        type_list = await self.get_type_list("blacklist")

        #  Blacklist Counts
        stmt_access_blacklist = select(
            func.count(AccessList.id).label('blacklist_total')
        ).where(AccessList.location_id == location_id, AccessList.type_access_list_id == type_list.id)

        res_access_blacklist_counts_raw = await self.session.execute(stmt_access_blacklist)
        res__access_blacklist_counts = res_access_blacklist_counts_raw.first()

        return KpisBlacklistResponse(
            total=res__access_blacklist_counts.blacklist_total,
        )

    async def get_kpis(self, user_id: int, location_id: int) -> KpisResponse:
        """Get Dashboard KPIs Counters"""

        user = await self.user_service.get_user_profile(user_id)
        if user.role != UserRole.SUPERADMIN:
            # Check if company user has access to the location
            location = await self.session.get(Location, location_id)
            if not location.company_id or location.company_id != user.company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not allowed for this location.",
                )

        # Historical Access Log Counts
        stmt_access_log = select(
            func.count(AccessLog.id).label('historical_total'),
            func.count().filter(cast(AccessLog.created_at, Date)
                                == date.today()).label('entries_today'),
            func.count().filter(and_(AccessLog.exit_date == None, cast(AccessLog.created_at, Date)
                                == date.today())).label('currently_inside'),
        ).where(AccessLog.location_id == location_id)

        res_access_log_counts_raw = await self.session.execute(stmt_access_log)
        res__access_log_counts = res_access_log_counts_raw.first()

        #  Access List Counts
        whitelist_counts = await self.get_kpis_whitelist(location_id)
        blacklist_counts = await self.get_kpis_blacklist(location_id)

        return KpisResponse(
            historical_total=res__access_log_counts.historical_total,
            entries_today=res__access_log_counts.entries_today,
            currently_inside=res__access_log_counts.currently_inside,
            whitelist=whitelist_counts,
            blacklist=blacklist_counts
        )
