"""Seed reference MEN curricula for Collège 3ème demo flows."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import async_session
from app.services.compliance_service import seed_men_reference_data


async def main() -> None:
    async with async_session() as session:
        result = await seed_men_reference_data(session)
    print(
        "men-curriculum-seed-ok "
        f"curricula_created={result['curricula_created']} "
        f"objectives_created={result['objectives_created']}"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
