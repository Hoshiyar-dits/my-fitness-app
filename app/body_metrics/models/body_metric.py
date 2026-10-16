from sqlalchemy import Column, Integer, BigInteger, Date, Numeric, DateTime, ForeignKey, UniqueConstraint, func
from app.database.database import Base

class BodyMetric(Base):
    __tablename__ = "body_metrics"
    __table_args__ = (UniqueConstraint("user_id", "log_date", name="uq_body_metrics_user_date"),)

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    log_date = Column(Date, nullable=False)
    weight_kg = Column(Numeric(5, 2), nullable=False)
    body_fat_pct = Column(Numeric(4, 1), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
