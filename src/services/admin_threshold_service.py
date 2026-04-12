import logging

logger = logging.getLogger(__name__)


async def set_category_threshold(category_name: str, threshold: float) -> dict:
    from src.database import get_async_session
    from src.models.job_category import JobCategory
    from sqlalchemy import select

    if not 0.0 <= threshold <= 1.0:
        return {"status": "error", "message": "Threshold must be between 0.0 and 1.0"}

    async for session in get_async_session():
        stmt = select(JobCategory).where(JobCategory.name == category_name)
        result = await session.execute(stmt)
        category = result.scalar_one_or_none()

        if category:
            category.similarity_threshold = threshold
        else:
            category = JobCategory(name=category_name, similarity_threshold=threshold)
            session.add(category)

        await session.flush()
        await session.commit()
        return {
            "status": "success",
            "category": category_name,
            "threshold": threshold,
        }
