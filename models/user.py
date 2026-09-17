import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """Database model for registered SaaS users (Teachers, Educators, Admins)."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True, index=True, comment="User email address")
    hashed_password = Column(String(255), nullable=False, comment="BCrypt hashed password")
    full_name = Column(String(100), nullable=True, comment="User full name")
    tier = Column(String(20), nullable=False, default="free", comment="Plan tier: 'free', 'pro', 'team'")
    paystack_customer_code = Column(String(100), nullable=True, index=True, comment="Paystack customer code")
    paystack_subscription_code = Column(String(100), nullable=True, comment="Paystack subscription code")
    monthly_generations_used = Column(Integer, default=0, nullable=False, comment="Generations used in current billing cycle")
    monthly_questions_generated = Column(Integer, default=0, nullable=False, comment="Total questions generated in current billing cycle")
    quota_reset_at = Column(DateTime(timezone=True), nullable=True, comment="Start timestamp of current 30-day quota cycle")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        from datetime import timezone, timedelta
        from utils.usage_limits import USER_TIER_LIMITS, USER_TIER_MAX_QUESTIONS, USER_TIER_MAX_MONTHLY_QUESTIONS
        tier = (self.tier or "free").lower()
        monthly_limit = USER_TIER_LIMITS.get(tier, USER_TIER_LIMITS["free"])
        max_questions = USER_TIER_MAX_QUESTIONS.get(tier, USER_TIER_MAX_QUESTIONS["free"])
        monthly_questions_limit = USER_TIER_MAX_MONTHLY_QUESTIONS.get(tier, USER_TIER_MAX_MONTHLY_QUESTIONS["free"])
        used = self.monthly_generations_used or 0
        remaining = max(0, monthly_limit - used)
        questions_used = self.monthly_questions_generated or 0
        questions_remaining = max(0, monthly_questions_limit - questions_used)

        now = datetime.now(timezone.utc)
        base_date = self.quota_reset_at or self.created_at or now
        if base_date.tzinfo is None:
            base_date = base_date.replace(tzinfo=timezone.utc)
        next_renewal = base_date + timedelta(days=30)
        days_until_reset = max(0, (next_renewal - now).days)

        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "tier": self.tier,
            "paystack_customer_code": self.paystack_customer_code,
            "monthly_generations_used": used,
            "monthly_limit": monthly_limit,
            "generations_remaining": remaining,
            "max_questions_per_quiz": max_questions,
            "monthly_questions_generated": questions_used,
            "monthly_questions_limit": monthly_questions_limit,
            "total_questions_remaining": questions_remaining,
            "is_quota_exhausted": remaining <= 0 or questions_remaining <= 0,
            "quota_reset_at": self.quota_reset_at.isoformat() if self.quota_reset_at else None,
            "next_renewal_date": next_renewal.strftime("%b %d, %Y"),
            "days_until_reset": days_until_reset,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

