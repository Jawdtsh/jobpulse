import pytest
import uuid
from datetime import datetime, timezone, timedelta

from src.models.job_match import JobMatch
from src.models.job import Job
from src.models.user import User
from src.models.user_cv import UserCV
from src.repositories.match_repository import MatchRepository
from src.services.matching_service import MatchingService
from src.services.metrics_service import MetricsService
from src.services.threshold_service import ThresholdService


@pytest.fixture
async def setup_data(db_session):
    user = User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        subscription_tier="pro",
    )
    db_session.add(user)
    await db_session.flush()

    job = Job(
        telegram_message_id=111,
        title="Backend Developer",
        company="TestCorp",
        description="Python developer",
        source_channel_id=None,
        embedding_vector=[0.1] * 768,
        content_hash="test_hash_matching_001",
    )
    db_session.add(job)
    await db_session.flush()

    cv = UserCV(
        user_id=user.id,
        title="My CV",
        content=b"encrypted",
        is_active=True,
        embedding_vector=[0.1] * 768,
    )
    db_session.add(cv)
    await db_session.flush()

    await db_session.commit()
    return user, job, cv


@pytest.mark.asyncio
async def test_end_to_end_matching(db_session, setup_data):
    user, job, cv = setup_data
    svc = MatchingService(db_session)
    results = await svc.match_new_job(job.id)
    await db_session.commit()

    assert len(results) >= 1
    assert results[0]["user_id"] == str(user.id)
    assert results[0]["similarity"] >= 0.80


@pytest.mark.asyncio
async def test_inactive_cv_excluded(db_session, setup_data):
    user, job, cv = setup_data
    cv.is_active = False
    await db_session.flush()
    await db_session.commit()

    svc = MatchingService(db_session)
    results = await svc.match_new_job(job.id)
    await db_session.commit()

    assert len(results) == 0


@pytest.mark.asyncio
async def test_null_embedding_skipped(db_session, setup_data):
    user, job, cv = setup_data
    job.embedding_vector = None
    await db_session.flush()
    await db_session.commit()

    svc = MatchingService(db_session)
    with pytest.raises(Exception):
        await svc.match_new_job(job.id)


@pytest.mark.asyncio
async def test_multi_cv_matching(db_session, setup_data):
    user, job, cv = setup_data

    cv2 = UserCV(
        user_id=user.id,
        title="Frontend CV",
        content=b"encrypted2",
        is_active=True,
        embedding_vector=[0.12] * 768,
    )
    db_session.add(cv2)
    await db_session.flush()
    await db_session.commit()

    svc = MatchingService(db_session)
    results = await svc.match_new_job(job.id)
    await db_session.commit()

    assert len(results) == 2


@pytest.mark.asyncio
async def test_match_click_tracking(db_session, setup_data):
    user, job, cv = setup_data
    repo = MatchRepository(db_session)
    match = await repo.create_match(
        job_id=job.id, user_id=user.id, similarity_score=0.92, cv_id=cv.id
    )
    await db_session.commit()

    assert match is not None
    assert match.is_clicked is False

    updated = await repo.mark_clicked(match.id)
    await db_session.commit()

    assert updated.is_clicked is True
    assert updated.clicked_at is not None


@pytest.mark.asyncio
async def test_threshold_priority(db_session, setup_data):
    user, job, cv = setup_data
    svc = ThresholdService(db_session)

    prefs = await svc.set_user_threshold(user.id, 0.85)
    await db_session.commit()

    assert prefs.similarity_threshold == 0.85

    threshold = await svc.get_effective_threshold(user.id)
    assert threshold == 0.85


@pytest.mark.asyncio
async def test_metrics_ctr(db_session, setup_data):
    user, job, cv = setup_data
    repo = MatchRepository(db_session)

    match = await repo.create_match(
        job_id=job.id, user_id=user.id, similarity_score=0.90, cv_id=cv.id
    )
    await repo.mark_notified(match.id)
    await repo.mark_clicked(match.id)
    await db_session.commit()

    metrics_svc = MetricsService(db_session)
    report = await metrics_svc.generate_report()

    assert report["ctr"]["total_notified"] >= 1
    assert report["ctr"]["total_clicked"] >= 1
