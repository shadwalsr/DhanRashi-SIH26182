import asyncio
import json
import logging
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import (
    BridgeRegistryModel,
    Case,
    Investigation,
    Org,
    Role,
    User,
    Vasp,
    VaspAddress,
)
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

DEMO_CASES = [
    {
        "ref": "CASE-DEMO-001",
        "title": "Case 1: Clean Single-Hop Exchange Deposit",
        "wallet": "0x0000000000000000000000000000000000aa0001",
        "chain": "ethereum",
        "description": "Direct single-hop transfer from target seed wallet to Binance deposit address.",
    },
    {
        "ref": "CASE-DEMO-002",
        "title": "Case 2: Pro-Rata Flow Ranking Proof (Hop-1 vs Hop-3)",
        "wallet": "0x0000000000000000000000000000000000aa0002",
        "chain": "ethereum",
        "description": "Demonstrates flow proportion ranking: hop-3 Kraken deposit receiving 88% outranks hop-1 Coinbase receiving 5%.",
    },
    {
        "ref": "CASE-DEMO-003",
        "title": "Case 3: Conflicting Entity Labels & Disputed Addresses",
        "wallet": "0x0000000000000000000000000000000000aa0003",
        "chain": "ethereum",
        "description": "Target address carries conflicting labels (OKX vs Huobi). CAP-04 applies, capping score to MEDIUM tier.",
    },
    {
        "ref": "CASE-DEMO-004",
        "title": "Case 4: High-Risk Laundering Trail (Mixer + Peel Chain)",
        "wallet": "0x0000000000000000000000000000000000aa0004",
        "chain": "ethereum",
        "description": "Mixer interaction (30) + rapid movement (18) + peel chain (24) yielding risk score 72 / HIGH.",
    },
    {
        "ref": "CASE-DEMO-005",
        "title": "Case 5: Cross-Chain Bridge Traversal (ETH -> Polygon)",
        "wallet": "0x0000000000000000000000000000000000aa0005",
        "chain": "ethereum",
        "description": "ETH bridge deposit matched to Polygon payout, continuing trace to QuickSwap DEX deposit.",
    },
]


async def seed_data(engine=None):
    if engine is None:
        try:
            test_engine = create_async_engine(settings.DATABASE_URL, echo=False)
            async with test_engine.connect() as conn:
                await conn.execute(select(1))
            engine = test_engine
        except Exception as e:  # noqa: BLE001
            logger.warning("Local PostgreSQL connection failed (%s). Seeding to SQLite fallback database.", e)
            engine = create_async_engine("sqlite+aiosqlite:///vasp_trace_demo.db", echo=False)

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
        user_map = {}
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
                await session.flush()
                logger.info("Created User: %s (%s)", user.email, u_data["role"])
            else:
                logger.info("User already exists: %s", user.email)
            user_map[u_data["email"]] = user

        inv_user = user_map["inv@vasptrace.internal"]

        # 4. Seed VASP Registry from JSON
        repo_root = Path(__file__).resolve()
        while repo_root.parent != repo_root:
            if (repo_root / "data" / "demo").exists():
                break
            repo_root = repo_root.parent
        registry_json_path = repo_root / "data" / "demo" / "registry" / "vasps.json"
        if registry_json_path.exists():
            data = json.loads(registry_json_path.read_text(encoding="utf-8"))
            for v_data in data.get("vasps", []):
                stmt = select(Vasp).where(Vasp.vasp_id == v_data["vasp_id"])
                res = await session.execute(stmt)
                vasp = res.scalar_one_or_none()
                if not vasp:
                    vasp = Vasp(
                        vasp_id=v_data["vasp_id"],
                        name=v_data["name"],
                        jurisdiction=v_data.get("jurisdiction"),
                        is_synthetic=v_data.get("is_synthetic", True),
                    )
                    session.add(vasp)
                    await session.flush()
                    logger.info("Created VASP: %s (%s)", vasp.name, vasp.vasp_id)

                for a_data in v_data.get("addresses", []):
                    stmt_addr = select(VaspAddress).where(VaspAddress.record_id == a_data["record_id"])
                    res_addr = await session.execute(stmt_addr)
                    if not res_addr.scalar_one_or_none():
                        v_addr = VaspAddress(
                            record_id=a_data["record_id"],
                            vasp_id_fk=vasp.id,
                            address=a_data["address"].lower(),
                            chain=a_data["chain"],
                            address_type=a_data["address_type"],
                            cluster_id=a_data.get("cluster_id"),
                            source=a_data["source"],
                            source_reference=a_data["source_reference"],
                            evidence_type=a_data["evidence_type"],
                            confidence=a_data["confidence"],
                            first_seen=date.fromisoformat(a_data["first_seen"]),
                            last_verified=date.fromisoformat(a_data["last_verified"]),
                            status=a_data["status"],
                            conflict=a_data.get("conflict", False),
                            is_synthetic=True,
                        )
                        session.add(v_addr)
                        logger.info("Added VASP Address: %s -> %s", a_data["address"], vasp.vasp_id)

            # Seed Bridge Registry
            for b_data in data.get("bridge_registry", []):
                stmt_b = select(BridgeRegistryModel).where(BridgeRegistryModel.bridge_id == b_data["bridge_id"])
                res_b = await session.execute(stmt_b)
                if not res_b.scalar_one_or_none():
                    bridge = BridgeRegistryModel(
                        bridge_id=b_data["bridge_id"],
                        name=b_data["name"],
                        source_chain=b_data["source_chain"],
                        destination_chain=b_data["destination_chain"],
                        source_contract_address=b_data["source_contract_address"].lower(),
                        destination_contract_address=b_data["destination_contract_address"].lower(),
                        event_abi_signature=b_data.get("event_abi_signature"),
                        fee_percentage=b_data.get("fee_percentage", 0.01),
                        max_time_window_seconds=b_data.get("max_time_window_seconds", 7200),
                        is_active=b_data.get("is_active", True),
                    )
                    session.add(bridge)
                    logger.info("Created Bridge Entry: %s", b_data["bridge_id"])
        else:
            logger.warning("VASP registry JSON file not found at %s", registry_json_path)

        # 5. Seed 5 Demo Cases and Investigations
        for case_info in DEMO_CASES:
            stmt_c = select(Case).where(Case.org_id == org.id, Case.reference_number == case_info["ref"])
            res_c = await session.execute(stmt_c)
            c_obj = res_c.scalar_one_or_none()
            if not c_obj:
                c_obj = Case(
                    reference_number=case_info["ref"],
                    title=case_info["title"],
                    description=case_info["description"],
                    org_id=org.id,
                    owner_id=inv_user.id,
                    status="ACTIVE",
                )
                session.add(c_obj)
                await session.flush()
                logger.info("Created Demo Case: %s", case_info["ref"])

            stmt_inv = select(Investigation).where(
                Investigation.case_id == c_obj.id,
                Investigation.wallet_address == case_info["wallet"].lower(),
            )
            res_inv = await session.execute(stmt_inv)
            if not res_inv.scalar_one_or_none():
                inv = Investigation(
                    case_id=c_obj.id,
                    wallet_address=case_info["wallet"].lower(),
                    blockchain=case_info["chain"],
                    depth=3,
                    min_usd_value=100.0,
                    status="CREATED",
                )
                session.add(inv)
                logger.info("Created Investigation for %s (%s)", case_info["wallet"], case_info["ref"])

        await session.commit()
        logger.info("Seeding completed successfully! 5 demo cases, VASP registry, and bridge entries loaded.")


def main():
    asyncio.run(seed_data())


if __name__ == "__main__":
    main()
