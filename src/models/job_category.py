from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import UUIDPrimaryKeyMixin, TimestampMixin
from src.database import Base


class JobCategory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "job_categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    similarity_threshold: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.80
    )
