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
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "tier": self.tier,
            "paystack_customer_code": self.paystack_customer_code,
            "monthly_generations_used": self.monthly_generations_used,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
