import asyncio
import sys
from pathlib import Path

from app.db.session import AsyncSessionLocal
from app.services.registry_import import import_registry_csv


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m app.scripts.import_registry <csv_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except OSError as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        result = await import_registry_csv(session, content)
        if result["errors"]:
            print(f"Errors during import ({len(result['errors'])} rows failed):")
            for error in result["errors"]:
                print(f"Row {error['row']}: {', '.join(error['errors'])}")
            print("\nTransaction aborted. Nothing was imported.")
            sys.exit(1)
        else:
            print(f"Successfully imported {result['imported']} records from {result['total_rows']} rows.")
            print(f"File hash: {result['file_hash']}")


if __name__ == "__main__":
    asyncio.run(main())
