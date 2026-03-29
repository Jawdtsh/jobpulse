import pytest
import uuid
from datetime import datetime, timezone
from src.models import (
    User,
    UserCV,
    Job,
    JobMatch,
    Subscription,
    ReferralReward,
    CoverLetterLog,
    UserInteraction,
    JobReport,
    ArchivedJob,
    TelegramSession,
    MonitoredChannel,
)


class TestUserModel:
    def test_user_creation(self):
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            referral_code="ABC12345",
            subscription_tier="free",
        )
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.referral_code == "ABC12345"
        assert user.subscription_tier == "free"

    def test_user_subscription_default(self):
        user = User(
            telegram_id=123456789,
            first_name="Test",
            referral_code="XYZ12345",
            subscription_tier="free",
        )
        assert user.subscription_tier == "free"


class TestUserCVModel:
    def test_cv_creation(self):
        cv = UserCV(
            user_id=uuid.uuid4(),
            title="My CV",
            content=b"encrypted_content",
            is_active=True,
        )
        assert cv.title == "My CV"
        assert cv.content == b"encrypted_content"
        assert cv.is_active == True


class TestJobModel:
    def test_job_creation(self):
        job = Job(
            telegram_message_id=12345,
            title="Software Engineer",
            company="Tech Corp",
            description="Great opportunity",
            is_archived=False,
            requirements=[],
            skills=[],
        )
        assert job.title == "Software Engineer"
        assert job.company == "Tech Corp"
        assert job.is_archived == False

    def test_job_default_requirements_skills(self):
        job = Job(
            telegram_message_id=12345,
            title="Engineer",
            company="Company",
            description="Description",
            requirements=[],
            skills=[],
        )
        assert job.requirements == []
        assert job.skills == []


class TestJobMatchModel:
    def test_job_match_creation(self):
        match = JobMatch(
            job_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            similarity_score=0.85,
            is_notified=False,
            is_clicked=False,
        )
        assert match.similarity_score == 0.85
        assert match.is_notified == False
        assert match.is_clicked == False


class TestSubscriptionModel:
    def test_subscription_creation(self):
        now = datetime.now(timezone.utc)
        sub = Subscription(
            user_id=uuid.uuid4(),
            plan_type="pro",
            amount=999,
            payment_method="stripe",
            valid_from=now,
            valid_until=now,
            status="active",
        )
        assert sub.plan_type == "pro"
        assert sub.amount == 999
        assert sub.status == "active"


class TestReferralRewardModel:
    def test_referral_reward_creation(self):
        now = datetime.now(timezone.utc)
        reward = ReferralReward(
            referrer_id=uuid.uuid4(),
            referred_user_id=uuid.uuid4(),
            reward_type="credits",
            reward_value=100,
            expires_at=now,
            status="pending",
        )
        assert reward.reward_type == "credits"
        assert reward.reward_value == 100
        assert reward.status == "pending"


class TestCoverLetterLogModel:
    def test_cover_letter_log_creation(self):
        log = CoverLetterLog(
            user_id=uuid.uuid4(),
            job_id=uuid.uuid4(),
        )
        assert log.user_id is not None
        assert log.job_id is not None


class TestUserInteractionModel:
    def test_user_interaction_creation(self):
        interaction = UserInteraction(
            user_id=uuid.uuid4(),
            action_type="button_click",
            action_data={"button": "apply"},
        )
        assert interaction.action_type == "button_click"
        assert interaction.action_data == {"button": "apply"}


class TestJobReportModel:
    def test_job_report_creation(self):
        report = JobReport(
            job_id=uuid.uuid4(),
            reporter_user_id=uuid.uuid4(),
            reason="spam",
        )
        assert report.reason == "spam"


class TestArchivedJobModel:
    def test_archived_job_creation(self):
        archived = ArchivedJob(
            original_job_id=uuid.uuid4(),
            telegram_message_id=12345,
            title="Old Job",
            company="Old Company",
            description="Old description",
            content_hash="abc123",
            archive_reason="retention",
        )
        assert archived.archive_reason == "retention"
        assert archived.original_job_id is not None


class TestTelegramSessionModel:
    def test_telegram_session_creation(self):
        session = TelegramSession(
            session_string=b"encrypted_session",
            phone_number="+1234567890",
            is_active=True,
            is_banned=False,
            use_count=0,
        )
        assert session.phone_number == "+1234567890"
        assert session.is_active == True
        assert session.is_banned == False
        assert session.use_count == 0


class TestMonitoredChannelModel:
    def test_monitored_channel_creation(self):
        channel = MonitoredChannel(
            username="jobpostings",
            title="Job Postings Channel",
            is_active=True,
            jobs_found=0,
            false_positives=0,
        )
        assert channel.username == "jobpostings"
        assert channel.title == "Job Postings Channel"
        assert channel.is_active == True
        assert channel.jobs_found == 0
