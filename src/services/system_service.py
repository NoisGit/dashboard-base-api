from datetime import date
from sqlmodel import select
from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, Location, AccessLog, Plan, UserLocationAccess, Company, CompanyStaff
from sqlalchemy.orm import aliased
from src.schemas import (
    SystemCountersResponse,
    SystemStatsResponse,
    MonthlyIncomeResponse,
    DetailAdminsResponse,
)


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

    async def get_system_detail_income_by_month(self) -> MonthlyIncomeResponse:
        """Get System detail income by month"""

        # Access Income by month
        stmt_income_by_month = select(
            func.count(AccessLog.id).label('quantity'),
            func.extract('month', AccessLog.created_at).label('month'),
            func.extract('year', AccessLog.created_at).label('year')
        ).group_by('year', 'month').order_by(desc('year'), desc('month'))
        result = await self.session.execute(stmt_income_by_month)

        res_income_by_month = result.mappings().all()

        return MonthlyIncomeResponse(detail_income_by_month=res_income_by_month)

    async def get_detail_admins(self) -> DetailAdminsResponse:
        """Get System Admin Details"""
        Janitor = aliased(User)

        # Admin Details
        stmt = (
            select(
                User.id.label("id_user"),
                User.full_name.label("name"),
                User.email.label("email"),
                func.coalesce(Company.logo, "").label("logo"),
                func.coalesce(Plan.name, "No Plan").label("plan"),
                User.created_at.label("creation_date"),
                func.coalesce(func.count(func.distinct(UserLocationAccess.id)), 0).label(
                    "entrances_count"),
                func.coalesce(func.count(func.distinct(Janitor.id)), 0).label(
                    "janitors_count")
            )
            .outerjoin(Plan, User.plan_id == Plan.id)
            .outerjoin(CompanyStaff, User.id == CompanyStaff.user_id)
            .outerjoin(Company, CompanyStaff.company_id == Company.id)
            .outerjoin(UserLocationAccess, User.id == UserLocationAccess.user_id)
            .outerjoin(Janitor, (CompanyStaff.user_id == Janitor.id) & (Janitor.role == 'JANITOR'))
            .where(User.role == 'ADMIN')
            .group_by(
                User.id,
                User.full_name,
                User.email,
                User.is_active,
                User.created_at,
                Plan.name,
                Company.logo
            )
            .order_by(desc(User.created_at))
        )

        result = await self.session.execute(stmt)

        res_detail_admins = result.mappings().all()

        return DetailAdminsResponse(detail_admins=res_detail_admins)

    async def get_system_stats(self) -> SystemStatsResponse:
        """Get System Stats"""
        counters = await self.get_system_counters()
        list_incomes = await self.get_system_detail_income_by_month()
        list_admins = await self.get_detail_admins()

        return {
            "status": "success",
            "message": "System stats retrieved successfully",
            "data": {
                "counters": counters,
                "detail_income_by_month": list_incomes.detail_income_by_month,
                "detail_admins": list_admins.detail_admins
            }
        }
