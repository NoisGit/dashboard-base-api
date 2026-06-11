"""Seed demo data for Locentr API."""

import asyncio
import os
from datetime import datetime

from sqlmodel import select

from src.core.enums import UserRole
from src.database import async_session, create_db_and_tables, engine
from src.models import User

DEMO_EMAIL = os.getenv("LOCENTR_DEMO_EMAIL", "admin@nois.dev")
DEMO_USERNAME = os.getenv("LOCENTR_DEMO_USERNAME", "locentr-admin")
DEMO_FULL_NAME = os.getenv("LOCENTR_DEMO_FULL_NAME", "Locentr Admin")
DEMO_CREDENTIAL_HASH = os.getenv("LOCENTR_DEMO_CREDENTIAL_HASH")


def get_demo_credential_hash() -> str:
    """Return the demo credential hash from environment."""
    if not DEMO_CREDENTIAL_HASH:
        raise RuntimeError("LOCENTR_DEMO_CREDENTIAL_HASH is required.")
    return DEMO_CREDENTIAL_HASH


async def seed_demo_user() -> None:
    """Create or update the demo admin user."""
    await create_db_and_tables()
    credential_hash = get_demo_credential_hash()

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.email == DEMO_EMAIL),
        )
        user = result.scalars().first()

        if user:
            user.username = DEMO_USERNAME
            user.full_name = DEMO_FULL_NAME
            user.role = UserRole.SUPERADMIN
            user.status = True
            user.is_active = True
            setattr(user, "password_hash", credential_hash)
            user.last_update = datetime.now()
            session.add(user)
            await session.commit()
            print(f"Updated demo user: {DEMO_EMAIL}")
            return

        user = User(
            username=DEMO_USERNAME,
            full_name=DEMO_FULL_NAME,
            email=DEMO_EMAIL,
            role=UserRole.SUPERADMIN,
            status=True,
            is_active=True,
            plan_id=None,
            created_at=datetime.now(),
            **{"password_hash": credential_hash},
        )

        session.add(user)
        await session.commit()
        print(f"Created demo user: {DEMO_EMAIL}")


async def main() -> None:
    """Run demo seed."""
    try:
        await seed_demo_user()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
