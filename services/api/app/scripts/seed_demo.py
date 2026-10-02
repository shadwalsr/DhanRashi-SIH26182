import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import Org, Role, User
from app.domain.enums import UserRole

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("seed_demo")

SEED_ROLES = [
    {"name": UserRole.INV.value, "description": "Investigator - runs investigations, reviews attribution"},
    {"name": UserRole.FIA.value, "description": "Financial Intelligence Analyst - registry curation & graph analysis"},
    {"name": UserRole.SUP.value, "description": "Supervisor - oversees cases, approves reports & SAHYOG submissions"},
    {"name": UserRole.AUD.value, "description": "Auditor - inspects immutable audit logs and verifies hash chain"},
    {"name": UserRole.ADM.value, "description": "Administrator - manages users, providers, keys, and system config"},
    {"name": UserRole.RO.value, "description": "Read-only Officer - views shared reports and read-only summaries"},
]

SEED_USERS = [
    {
        "email": "inv@vasptrace.internal",
        "password": "investigator123",
        "full_name": "Inspector Roy",
        "role": UserRole.INV.value,
    },
    {
        "email": "fia@vasptrace.internal",
        "password": "analyst123",
        "full_name": "Analyst Sharma",
        "role": UserRole.FIA.value,
    },
    {
        "email": "sup@vasptrace.internal",
        "password": "supervisor123",
        "full_name": "Superintendent Verma",
        "role": UserRole.SUP.value,
    },
    {
        "email": "aud@vasptrace.internal",
        "password": "auditor123",
        "full_name": "Auditor Menon",
        "role": UserRole.AUD.value,
    },
    {
        "email": "adm@vasptrace.internal",
        "password": "admin123",
        "full_name": "Admin Gupta",
        "role": UserRole.ADM.value,
    },
    {
        "email": "ro@vasptrace.internal",
        "password": "readonly123",
        "full_name": "Officer Das",
        "role": UserRole.RO.value,
    },
]


async def seed_data(engine=None):
    if engine is None:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # 1. Seed or retrieve Demo Organization
        stmt = select(Org).where(Org.code == "CCU-DEMO")
        res = await session.execute(stmt)
        org = res.scalar_one_or_none()
        if not org:
            org = Org(name="Cyber Crime Unit - Demo", code="CCU-DEMO")
            session.add(org)
            await session.flush()
            logger.info("Created Demo Org: %s (%s)", org.name, org.code)
        else:
            logger.info("Org already exists: %s", org.name)

        # 2. Seed Roles
        role_map = {}
        for r_data in SEED_ROLES:
            stmt = select(Role).where(Role.name == r_data["name"])
            res = await session.execute(stmt)
            role = res.scalar_one_or_none()
            if not role:
                role = Role(name=r_data["name"], description=r_data["description"])
                session.add(role)
                await session.flush()
                logger.info("Created Role: %s", role.name)
            role_map[role.name] = role

        # 3. Seed Users (one per role)
        for u_data in SEED_USERS:
            stmt = select(User).where(User.email == u_data["email"])
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                role_obj = role_map[u_data["role"]]
                user = User(
                    email=u_data["email"],
                    hashed_password=get_password_hash(u_data["password"]),
                    full_name=u_data["full_name"],
                    role_id=role_obj.id,
                    org_id=org.id,
                    is_active=True,
                )
                session.add(user)
                logger.info("Created User: %s (%s)", user.email, u_data["role"])
            else:
                logger.info("User already exists: %s", user.email)

        await session.commit()
        logger.info("Seeding completed successfully!")


def main():
    asyncio.run(seed_data())


if __name__ == "__main__":
    main()
