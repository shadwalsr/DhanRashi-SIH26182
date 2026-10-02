"""Demo seeder stub for Phase 0 / Phase 1."""
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_demo")


def seed_demo_data() -> None:
    logger.info("Initializing demo dataset seeding...")
    logger.info("Phase 0: Stub ready. Will populate synthetic cases and fixtures in Phase 1 & 2.")


if __name__ == "__main__":
    seed_demo_data()
