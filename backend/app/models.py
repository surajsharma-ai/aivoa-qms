from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="Draft")
    risk_level: Mapped[str] = mapped_column(String(16), default="Pending")
    source: Mapped[str] = mapped_column(String(32), default="Email")
    reporter: Mapped[str] = mapped_column(String(160), default="—")
    product_name: Mapped[str] = mapped_column(String(160), default="—")
    batch_number: Mapped[str] = mapped_column(String(80), default="—")
    complaint_category: Mapped[str] = mapped_column(String(80), default="—")
    summary: Mapped[str] = mapped_column(Text, default="")
    form_data: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_assessment: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
