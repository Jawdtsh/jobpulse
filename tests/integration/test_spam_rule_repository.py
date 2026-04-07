import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.spam_rule_repository import SpamRuleRepository


@pytest_asyncio.fixture
async def repo(db_session: AsyncSession) -> SpamRuleRepository:
    return SpamRuleRepository(db_session)


class TestCRUD:
    @pytest.mark.asyncio
    async def test_create_rule(self, repo: SpamRuleRepository):
        rule = await repo.create(pattern="إعلان", rule_type="spam_keyword")
        assert rule.pattern == "إعلان"
        assert rule.rule_type == "spam_keyword"
        assert rule.is_active is True

    @pytest.mark.asyncio
    async def test_get_rule(self, repo: SpamRuleRepository):
        created = await repo.create(pattern="scam", rule_type="scam_indicator")
        fetched = await repo.get(created.id)
        assert fetched is not None
        assert fetched.pattern == "scam"

    @pytest.mark.asyncio
    async def test_update_rule(self, repo: SpamRuleRepository):
        created = await repo.create(pattern="test", rule_type="spam_keyword")
        updated = await repo.update(created.id, is_active=False)
        assert updated is not None
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_delete_rule(self, repo: SpamRuleRepository):
        created = await repo.create(pattern="delete_me", rule_type="spam_keyword")
        deleted = await repo.delete(created.id)
        assert deleted is True
        assert await repo.get(created.id) is None


class TestGetActiveRules:
    @pytest.mark.asyncio
    async def test_returns_only_active(self, repo: SpamRuleRepository):
        await repo.create(pattern="active_rule", rule_type="spam_keyword")
        inactive = await repo.create(pattern="inactive_rule", rule_type="spam_keyword")
        await repo.update(inactive.id, is_active=False)

        active = await repo.get_active_rules()
        assert len(active) == 1
        assert active[0].pattern == "active_rule"

    @pytest.mark.asyncio
    async def test_returns_empty_when_none(self, repo: SpamRuleRepository):
        active = await repo.get_active_rules()
        assert active == []


class TestUniqueConstraint:
    @pytest.mark.asyncio
    async def test_duplicate_pattern_type_rejected(self, repo: SpamRuleRepository):
        from sqlalchemy.exc import IntegrityError

        await repo.create(pattern="duplicate", rule_type="spam_keyword")
        with pytest.raises(IntegrityError):
            await repo.create(pattern="duplicate", rule_type="spam_keyword")

    @pytest.mark.asyncio
    async def test_same_pattern_different_type_allowed(self, repo: SpamRuleRepository):
        r1 = await repo.create(pattern="test_pattern", rule_type="spam_keyword")
        r2 = await repo.create(pattern="test_pattern", rule_type="scam_indicator")
        assert r1.id != r2.id


class TestRuleTypeValidation:
    @pytest.mark.asyncio
    async def test_valid_spam_keyword(self, repo: SpamRuleRepository):
        rule = await repo.create(pattern="kw", rule_type="spam_keyword")
        assert rule.rule_type == "spam_keyword"

    @pytest.mark.asyncio
    async def test_valid_scam_indicator(self, repo: SpamRuleRepository):
        rule = await repo.create(pattern="ind", rule_type="scam_indicator")
        assert rule.rule_type == "scam_indicator"
