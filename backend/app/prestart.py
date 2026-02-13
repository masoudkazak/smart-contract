import asyncio

from loguru import logger

from .db import ping_database


async def _wait_for_db(max_attempts: int = 30, delay_seconds: float = 2.0) -> None:
    attempt = 0
    while True:
        attempt += 1
        try:
            logger.info(f"Trying to connect to database (attempt {attempt})...")
            await ping_database()
            logger.info("Database is available.")
            return
        except Exception as exc:  # noqa: BLE001
            if attempt >= max_attempts:
                logger.error(f"Database is not available after {attempt} attempts: {exc}")
                raise
            logger.warning(f"Database not ready yet ({exc}), retrying in {delay_seconds} seconds...")
            await asyncio.sleep(delay_seconds)


def main() -> None:
    asyncio.run(_wait_for_db())


if __name__ == "__main__":
    main()

