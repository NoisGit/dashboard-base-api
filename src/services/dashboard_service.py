from datetime import date
from sqlmodel import select
from sqlalchemy import func, desc, and_, cast, Date, case, distinct
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.enums import UserRole
from src.services import UserService

from src.models import AccessLog, AccessList, TypeAccessList, Location, ExternalPeople

from src.schemas import (
    KpisResponse,
    KpisBlacklistResponse,
    KpisWhitelistResponse,
    EntriesByMonthResponse,
    GenderDistributionResponse,
    ChartStatsResponse,
    DashboardStatsResponse,
    RecentEntriesResponse
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

    async def get_kpis(self, location_id: int) -> KpisResponse:
        """Get Dashboard KPIs Counters"""

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

    async def get_system_detail_income_by_month(self, location_id: int) -> EntriesByMonthResponse:
        """Get System detail income by month on current year"""

        # Translate month number to month name
        meses_case = case(
            (func.extract('month', AccessLog.created_at) == 1, 'Enero'),
            (func.extract('month', AccessLog.created_at) == 2, 'Febrero'),
            (func.extract('month', AccessLog.created_at) == 3, 'Marzo'),
            (func.extract('month', AccessLog.created_at) == 4, 'Abril'),
            (func.extract('month', AccessLog.created_at) == 5, 'Mayo'),
            (func.extract('month', AccessLog.created_at) == 6, 'Junio'),
            (func.extract('month', AccessLog.created_at) == 7, 'Julio'),
            (func.extract('month', AccessLog.created_at) == 8, 'Agosto'),
            (func.extract('month', AccessLog.created_at) == 9, 'Septiembre'),
            (func.extract('month', AccessLog.created_at) == 10, 'Octubre'),
            (func.extract('month', AccessLog.created_at) == 11, 'Noviembre'),
            (func.extract('month', AccessLog.created_at) == 12, 'Diciembre')
        )

        # Access Income by month on current year
        stmt_income_by_month = select(
            func.count(AccessLog.id).label('count'),
            meses_case.label('month'),
        ).where(AccessLog.location_id == location_id, func.extract('year', AccessLog.created_at) == date.today().year
                ).group_by(func.extract('month', AccessLog.created_at), meses_case
                           ).order_by(func.extract('month', AccessLog.created_at))
        result = await self.session.execute(stmt_income_by_month)

        res_income_by_month = result.mappings().all()

        return EntriesByMonthResponse(entries_by_month=res_income_by_month)

    async def get_gender_distribution(self, location_id: int):
        """Get Gender Distribution From Location on current year"""

        # Define cases for genders
        male_distinct_id = case((ExternalPeople.gender == '1', 1), else_=0)
        female_distinct_id = case((ExternalPeople.gender == '2', 1), else_=0)

        stmt_gender_distribution = (
            select(
                func.count(AccessLog.id).label('total'),
                func.count(distinct(male_distinct_id)).label('male_count'),
                func.count(distinct(female_distinct_id)).label('female_count')
            )
            .join(ExternalPeople, AccessLog.external_people_id == ExternalPeople.id)
            .where(AccessLog.location_id == location_id, func.extract('year', AccessLog.created_at) == date.today().year)
        )

        result_gender_distribution = await self.session.execute(stmt_gender_distribution)
        data_gender_distribution = result_gender_distribution.mappings().one()

        total = data_gender_distribution['total'] or 1

        # Calculate percentages
        distribution_male = round(
            (data_gender_distribution['male_count'] or 0) / total * 100, 2)
        distribution_female = round(
            (data_gender_distribution['female_count'] or 0) / total * 100, 2)

        return GenderDistributionResponse(
            male=distribution_male,
            female=distribution_female
        )

    async def get_charts_stats(self, location_id: int):
        """Get Charts Stats"""

        # Entries by month
        entries_by_month = await self.get_system_detail_income_by_month(location_id)
        # Gender distribution
        gender_distribution = await self.get_gender_distribution(location_id)

        return ChartStatsResponse(
            gender_distribution=gender_distribution,
            entries_by_month=entries_by_month
        )

    async def get_recent_entries(self, location_id: int) -> RecentEntriesResponse:
        """Get System last 3 entries from Location"""

        stmt_recent_entries = (
            select(
                ExternalPeople.name,
                ExternalPeople.id_number.label("identifier"),
                AccessLog.office.label("destination"),
                AccessLog.created_at.label("timestamp"),
            )
            .join(ExternalPeople, AccessLog.external_people_id == ExternalPeople.id)
            .where(AccessLog.location_id == location_id)
            .order_by(desc(AccessLog.created_at))
            .limit(3)
        )

        result_recent_entries = await self.session.execute(stmt_recent_entries)

        recent_entries = result_recent_entries.mappings().all()

        return recent_entries

    async def get_dashboard_stats(self, user_id: int, location_id: int) -> DashboardStatsResponse:
        """Get Dashboard KPIs Counters"""

        # Check company user access to location
        user = await self.user_service.get_user_profile(user_id)
        if user.role != UserRole.SUPERADMIN:
            # Check if company user has access to the location
            location = await self.session.get(Location, location_id)
            if not location or not location.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Location not found.",
                )
            if not location.company_id or location.company_id != user.company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not allowed for this location.",
                )

        #  Access to Stats Functions
        kpis_result = await self.get_kpis(location_id)
        charts_result = await self.get_charts_stats(location_id)
        recent_entries_result = await self.get_recent_entries(location_id)

        return DashboardStatsResponse(
            kpis=kpis_result,
            charts=charts_result,
            recent_entries=recent_entries_result
        )
