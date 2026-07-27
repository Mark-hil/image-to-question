import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Tenant(Base):
    """Database model for B2B API Customers / Organizations."""
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="Organization or customer name")
    email = Column(String(255), nullable=False, unique=True, index=True, comment="Primary contact email")
    tier = Column(String(20), nullable=False, default="starter", comment="Tier: 'starter', 'growth', 'enterprise'")
    paystack_customer_code = Column(String(100), nullable=True, index=True, comment="Paystack customer code (CUS_...)")
    paystack_subscription_code = Column(String(100), nullable=True, comment="Paystack subscription code (SUB_...)")
    is_active = Column(Boolean, default=True, nullable=False)
    monthly_quota = Column(Integer, default=1000, nullable=False, comment="Monthly request quota")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "tier": self.tier,
            "paystack_customer_code": self.paystack_customer_code,
            "is_active": self.is_active,
            "monthly_quota": self.monthly_quota,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class APIKey(Base):
    """Database model for API keys issued to Tenants."""
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, default="Default Key", comment="Name or label for key")
    key_prefix = Column(String(20), nullable=False, index=True, comment="First few characters for identification")
    key_hash = Column(String(128), nullable=False, unique=True, index=True, comment="SHA256 hash of raw API secret key")
    rate_limit_rpm = Column(Integer, default=60, nullable=False, comment="Requests per minute limit")
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant = relationship("Tenant", back_populates="api_keys")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "rate_limit_rpm": self.rate_limit_rpm,
            "is_active": self.is_active,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
