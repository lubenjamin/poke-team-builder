from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class IngestionError(Base):
    """
    Records data-validation failures during ingestion.
    """

    __tablename__ = "ingestion_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)  # 'batch' | 'scan'
    reason: Mapped[str] = mapped_column(String, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
