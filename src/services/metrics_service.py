import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job_match import JobMatch
from src.repositories.match_repository import MatchRepository

logger = logging.getLogger(__name__)

LOW_CTR_THRESHOLD = 0.05


class MetricsService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._match_repo: Optional[MatchRepository] = None

    @property
    def match_repo(self) -> MatchRepository:
        if self._match_repo is None:
            self._match_repo = MatchRepository(self._session)
        return self._match_repo

    async def calculate(self, user_id: uuid.UUID) -> dict:
        matches = await self.match_repo.get_matches_by_user(user_id)

        score_buckets: dict[str, dict] = {
            "0.00-0.60": {"count": 0, "clicked": 0, "notified": 0},
            "0.60-0.80": {"count": 0, "clicked": 0, "notified": 0},
            "0.80-1.00": {"count": 0, "clicked": 0, "notified": 0},
        }

        for match in matches:
            score = match.similarity_score
            is_clicked = bool(match.is_clicked)
            is_notified = bool(match.is_notified)

            if score < 0.60:
                bucket = score_buckets["0.00-0.60"]
            elif score < 0.80:
                bucket = score_buckets["0.60-0.80"]
            else:
                bucket = score_buckets["0.80-1.00"]

            bucket["count"] += 1
            if is_clicked:
                bucket["clicked"] += 1
            if is_notified:
                bucket["notified"] += 1

        ctr_data: dict[str, float] = {}
        for bucket_name, data in score_buckets.items():
            notified_count = data["notified"]
            if notified_count > 0:
                ctr = (data["clicked"] / notified_count) * 100
                ctr_data[bucket_name] = round(ctr, 2)
            else:
                ctr_data[bucket_name] = 0.0

        warnings: list[str] = []
        for bucket_name, ctr in ctr_data.items():
            if ctr < 5.0:
                warnings.append(
                    f"CTR for {bucket_name} is {ctr:.2f}%, below 5% threshold"
                )

        return {
            "score_buckets": {k: v["count"] for k, v in score_buckets.items()},
            "ctr_data": ctr_data,
            "warnings": warnings,
        }

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
