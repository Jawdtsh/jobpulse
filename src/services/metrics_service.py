import logging
from datetime import datetime, timezone

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job_match import JobMatch

logger = logging.getLogger(__name__)

LOW_CTR_THRESHOLD = 0.05


class MetricsService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def calculate_ctr(self) -> dict:
        stmt = select(
            func.count().label("total_notified"),
            func.sum(case((JobMatch.is_clicked, 1), else_=0)).label("total_clicked"),
        ).where(JobMatch.is_notified.is_(True))

        result = await self._session.execute(stmt)
        row = result.one()
        total_notified = row.total_notified or 0
        total_clicked = row.total_clicked or 0

        ctr = total_clicked / total_notified if total_notified > 0 else 0.0

        return {
            "total_notified": total_notified,
            "total_clicked": total_clicked,
            "ctr": round(ctr, 4),
        }

    async def get_score_distribution(self) -> dict:
        stmt = select(JobMatch.similarity_score).where(JobMatch.is_notified.is_(True))
        result = await self._session.execute(stmt)
        scores = [row[0] for row in result.all()]

        if not scores:
            return {"count": 0, "distribution": {}}

        buckets = {
            "0.60-0.70": 0,
            "0.70-0.80": 0,
            "0.80-0.90": 0,
            "0.90-1.00": 0,
        }
        for s in scores:
            if s < 0.70:
                buckets["0.60-0.70"] += 1
            elif s < 0.80:
                buckets["0.70-0.80"] += 1
            elif s < 0.90:
                buckets["0.80-0.90"] += 1
            else:
                buckets["0.90-1.00"] += 1

        return {"count": len(scores), "distribution": buckets}

    async def check_low_performing(self) -> list[str]:
        metrics = await self.calculate_ctr()
        warnings = []
        if metrics["ctr"] < LOW_CTR_THRESHOLD and metrics["total_notified"] > 10:
            warnings.append(
                f"Overall CTR {metrics['ctr']:.2%} is below {LOW_CTR_THRESHOLD:.0%} threshold"
            )
        return warnings

    async def generate_report(self) -> dict:
        ctr = await self.calculate_ctr()
        distribution = await self.get_score_distribution()
        warnings = await self.check_low_performing()

        report = {
            "ctr": ctr,
            "score_distribution": distribution,
            "warnings": warnings,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "Match quality report: CTR=%s, warnings=%d", ctr["ctr"], len(warnings)
        )
        return report
