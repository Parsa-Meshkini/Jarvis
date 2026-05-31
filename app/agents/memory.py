import logging
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.task import UserMemory

logger = logging.getLogger(__name__)

# Default user ID — single user system for now
DEFAULT_USER = "default"


async def save_preference(key: str, value: str, user_id: str = DEFAULT_USER) -> None:
    """Save or update a user preference in the database."""
    async with AsyncSessionLocal() as db:
        # Check if key already exists
        result = await db.execute(
            select(UserMemory)
            .where(UserMemory.user_id == user_id)
            .where(UserMemory.key == key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = value
        else:
            db.add(UserMemory(user_id=user_id, key=key, value=value))

        await db.commit()
        logger.info(f"[Memory] Saved {key} = {value}")


async def get_preference(key: str, default: str = "", user_id: str = DEFAULT_USER) -> str:
    """Get a single preference by key."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserMemory)
            .where(UserMemory.user_id == user_id)
            .where(UserMemory.key == key)
        )
        record = result.scalar_one_or_none()
        return record.value if record else default


async def get_all_preferences(user_id: str = DEFAULT_USER) -> dict:
    """Get all preferences for a user as a dict."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        records = result.scalars().all()
        return {r.key: r.value for r in records}


async def delete_preference(key: str, user_id: str = DEFAULT_USER) -> None:
    """Delete a preference."""
    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(UserMemory)
            .where(UserMemory.user_id == user_id)
            .where(UserMemory.key == key)
        )
        await db.commit()


async def build_user_context(user_id: str = DEFAULT_USER) -> dict:
    """
    Builds a context dict passed to the planner.
    Jarvis uses this to personalise every task.
    """
    prefs = await get_all_preferences(user_id=user_id)
    return {
        "location":          prefs.get("location", "Toronto, ON"),
        "preferred_time":    prefs.get("preferred_time", "afternoon"),
        "preferred_service": prefs.get("preferred_service", ""),
        "name":              prefs.get("name", ""),
        "phone":             prefs.get("phone", ""),
        "notes":             prefs.get("notes", ""),
    }