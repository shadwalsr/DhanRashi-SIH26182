"""VASP registry importer stub for Phase 2."""
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("import_registry")


def import_registry(file_path: str = "") -> None:
    logger.info("Import registry called with path: %s", file_path)
    logger.info("Phase 0: Importer stub ready for Phase 2 implementation.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else ""
    import_registry(path)
