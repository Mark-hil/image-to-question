# utils/usage_limits.py
"""
Centralized configuration and helper functions for usage limits,
tier quotas, and question count ceilings across B2C Users and B2B Tenants.
"""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.tenant import Tenant, APIKey
from utils.exceptions import AppError
from utils.auth import decode_access_token
from utils.rate_limit import check_rate_limit

# Monthly generation limits by User Tier (B2C Educators) - Industry Standard
USER_TIER_LIMITS: Dict[str, int] = {
    "free": 6,           # 6 quiz generations / uploads per month (approx 1-2 per week)
    "pro": 50,          # 50 document uploads / month (approx 10-12 per week)
    "team": 250,        # 250 document uploads / month (shared across 5 seats)
    "institution": 750  # 750 document uploads / month (campus/department-wide)
}

# Maximum questions allowed per single generation / upload by Tier
USER_TIER_MAX_QUESTIONS: Dict[str, int] = {
    "guest": 5,          # 5 questions per quiz
    "free": 20,          # 20 questions per quiz
    "pro": 35,           # 35 questions per quiz (typical classroom exam size)
    "team": 50,          # 50 questions per quiz
    "institution": 100   # 100 questions per quiz
}

# Total maximum questions allowed across all uploads per month
USER_TIER_MAX_MONTHLY_QUESTIONS: Dict[str, int] = {
    "free": 120,          # 120 total questions / month (6 uploads * 20 Qs)
    "pro": 1000,          # 1,000 total questions / month (50 uploads * 20-35 Qs)
    "team": 5000,         # 5,000 total questions / month (250 uploads across 5 seats)
    "institution": 15000  # 15,000 total questions / month (campus-wide)
}

# Default initial quota credits for B2B Tenants upon registration
DEFAULT_TENANT_INITIAL_QUOTA: int = 1000


# Top-up credit pack size for B2B Tenants on successful payment
DEFAULT_TENANT_TOPUP_CREDITS: int = 10000

@dataclass
class CallerIdentity:
    kind: str  # "user" | "tenant" | "guest"
    user: Optional[User] = None
    tenant: Optional[Tenant] = None
    api_key_obj: Optional[APIKey] = None
    max_questions: int = 5
    tier: str = "guest"

    @property
    def identifier(self) -> str:
        if self.user:
            return f"user:{self.user.id}"
        if self.tenant:
            return f"tenant:{self.tenant.id}"
        return "guest"

def refresh_user_quota_if_due(user: User) -> bool:
    """
    Checks if 30 days have elapsed since the user's last billing/quota cycle.
    If 30 days have passed, automatically resets `monthly_generations_used` and
    `monthly_questions_generated` to 0 and rolls forward `quota_reset_at`.
    Returns True if quota was renewed, False otherwise.
    """
    now = datetime.now(timezone.utc)
    base_date = user.quota_reset_at or user.created_at
    if base_date:
        if base_date.tzinfo is None:
            base_date = base_date.replace(tzinfo=timezone.utc)
        cycle_delta = timedelta(days=30)
        if now >= base_date + cycle_delta:
            cycles_passed = max(1, int((now - base_date) / cycle_delta))
            user.quota_reset_at = base_date + (cycle_delta * cycles_passed)
            user.monthly_generations_used = 0
            user.monthly_questions_generated = 0
            return True
    elif user.quota_reset_at is None:
        user.quota_reset_at = now
    return False

def get_user_quota_info(user: User) -> Dict[str, Any]:
    """Calculate and return tier limit, used count, and remaining generations & questions for a user."""
    refresh_user_quota_if_due(user)
    tier = (user.tier or "free").lower()
    limit = USER_TIER_LIMITS.get(tier, USER_TIER_LIMITS["free"])
    used = user.monthly_generations_used or 0
    remaining = max(0, limit - used)
    max_questions = USER_TIER_MAX_QUESTIONS.get(tier, USER_TIER_MAX_QUESTIONS["free"])

    monthly_questions_limit = USER_TIER_MAX_MONTHLY_QUESTIONS.get(tier, USER_TIER_MAX_MONTHLY_QUESTIONS["free"])
    questions_used = user.monthly_questions_generated or 0
    questions_remaining = max(0, monthly_questions_limit - questions_used)

    now = datetime.now(timezone.utc)
    base_date = user.quota_reset_at or user.created_at or now
    if base_date.tzinfo is None:
        base_date = base_date.replace(tzinfo=timezone.utc)
    next_renewal = base_date + timedelta(days=30)
    days_until_reset = max(0, (next_renewal - now).days)

    is_exhausted = (remaining <= 0) or (questions_remaining <= 0)

    return {
        "tier": tier,
        "monthly_limit": limit,
        "monthly_generations_used": used,
        "generations_remaining": remaining,
        "max_questions_per_quiz": max_questions,
        "monthly_questions_limit": monthly_questions_limit,
        "monthly_questions_generated": questions_used,
        "total_questions_remaining": questions_remaining,
        "is_quota_exhausted": is_exhausted,
        "renewal_date": next_renewal.strftime("%b %d, %Y"),
        "days_until_reset": days_until_reset
    }

def check_user_quota(user: User) -> Tuple[bool, Optional[str]]:
    """
    Returns (True, None) if user has remaining generations in their billing cycle.
    Returns (False, error_message) if quota is exhausted.
    """
    quota_info = get_user_quota_info(user)
    tier_title = quota_info["tier"].capitalize()
    if quota_info["generations_remaining"] <= 0:
        limit = quota_info["monthly_limit"]
        return False, (
            f"Monthly upload limit ({limit} quizzes) reached for your {tier_title} plan. "
            f"Your quota renews on {quota_info['renewal_date']}. Please upgrade to Pro for 100 uploads/month."
        )
    if quota_info["total_questions_remaining"] <= 0:
        q_limit = quota_info["monthly_questions_limit"]
        pro_q_limit = USER_TIER_MAX_MONTHLY_QUESTIONS.get("pro", 1000)
        return False, (
            f"Monthly total question generation limit ({q_limit} questions) reached for your {tier_title} plan. "
            f"Your quota renews on {quota_info['renewal_date']}. Please upgrade to Pro for {pro_q_limit:,} questions/month."
        )
    return True, None

def check_tenant_quota(tenant: Tenant) -> Tuple[bool, Optional[str]]:
    """
    Returns (True, None) if tenant has positive API quota remaining.
    Returns (False, error_message) if tenant quota is depleted.
    """
    if (tenant.monthly_quota or 0) <= 0:
        return False, (
            "API credit quota exhausted. Please top up your balance in the Developer Portal "
            "to continue generating questions."
        )
    return True, None

def validate_question_count(identity: CallerIdentity, requested_questions: int) -> int:
    """
    Validates whether the requested question count exceeds the tier's per-upload limit
    or exceeds the user's remaining monthly question quota.
    Raises AppError (400 or 402) if limits are exceeded.
    """
    max_allowed = identity.max_questions
    tier_title = identity.tier.capitalize()

    # 1. Per-upload maximum question check
    if requested_questions > max_allowed:
        pro_limit = USER_TIER_MAX_QUESTIONS["pro"]
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="TIER_QUESTION_LIMIT_EXCEEDED",
            message=(
                f"Your {tier_title} plan allows a maximum of {max_allowed} questions per upload. "
                f"You requested {requested_questions} questions. Please select {max_allowed} or fewer questions, "
                f"or upgrade to Pro to generate up to {pro_limit} questions per upload."
            )
        )

    # 2. Monthly total questions budget check for registered users
    if identity.kind == "user" and identity.user:
        quota_info = get_user_quota_info(identity.user)
        remaining_q = quota_info.get("total_questions_remaining", 999999)
        if remaining_q <= 0:
            raise AppError(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                error_code="PLAN_LIMIT_REACHED",
                message=(
                    f"Monthly total question limit ({quota_info['monthly_questions_limit']} questions) reached for your {tier_title} plan. "
                    f"Your quota renews on {quota_info['renewal_date']}. Please upgrade to Pro to continue generating."
                )
            )
        if requested_questions > remaining_q:
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="MONTHLY_QUESTION_BUDGET_EXCEEDED",
                message=(
                    f"This upload requests {requested_questions} questions, but you only have {remaining_q} questions left "
                    f"in your monthly allowance ({quota_info['monthly_questions_limit']} max). "
                    f"Please adjust to {remaining_q} or fewer questions, or upgrade to Pro."
                )
            )

    return max(1, min(requested_questions, max_allowed))

async def resolve_and_enforce_identity(
    db: AsyncSession,
    authorization: Optional[str] = None,
    x_api_key: Optional[str] = None,
    teacher_id: Optional[str] = None,
) -> CallerIdentity:
    """
    Validates caller identity, verifies authentication credentials,
    checks rate limits, and enforces usage quotas.
    Raises AppError (401, 403, 402, 429) if validation or quota fails.
    """
    # 1. B2B Tenant via X-API-Key
    if x_api_key and x_api_key.strip():
        raw_key = x_api_key.strip()
        hashed_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        stmt = select(APIKey).where(
            APIKey.key_hash == hashed_key,
            APIKey.is_active == True
        )
        res = await db.execute(stmt)
        api_key_obj = res.scalar_one_or_none()

        if not api_key_obj:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_API_KEY",
                message="Provided API Key is invalid or inactive."
            )

        tenant_stmt = select(Tenant).where(
            Tenant.id == api_key_obj.tenant_id,
            Tenant.is_active == True
        )
        tenant_res = await db.execute(tenant_stmt)
        tenant = tenant_res.scalar_one_or_none()

        if not tenant:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="TENANT_INACTIVE",
                message="The organization associated with this API key is inactive."
            )

        # Check Rate Limit (RPM)
        if not check_rate_limit(tenant.id, limit_rpm=api_key_obj.rate_limit_rpm or 60):
            raise AppError(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                error_code="RATE_LIMIT_EXCEEDED",
                message=f"Rate limit exceeded ({api_key_obj.rate_limit_rpm} RPM). Please throttle requests."
            )

        # Check Tenant Quota
        quota_ok, err_msg = check_tenant_quota(tenant)
        if not quota_ok:
            raise AppError(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                error_code="QUOTA_EXHAUSTED",
                message=err_msg
            )

        # Update last_used_at timestamp
        api_key_obj.last_used_at = datetime.utcnow()
        await db.commit()

        return CallerIdentity(
            kind="tenant",
            tenant=tenant,
            api_key_obj=api_key_obj,
            max_questions=100,
            tier=tenant.tier
        )

    # 2. B2C User via JWT Bearer Token
    if authorization and authorization.strip():
        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_TOKEN",
                message="Invalid or expired authentication token."
            )

        user_stmt = select(User).where(User.id == payload["sub"])
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="USER_NOT_FOUND",
                message="User account not found."
            )

        if not user.is_active:
            raise AppError(
                status_code=status.HTTP_403_FORBIDDEN,
                error_code="USER_DEACTIVATED",
                message="User account is deactivated."
            )

        # Auto-renew quota if cycle has completed
        if refresh_user_quota_if_due(user):
            await db.commit()
            await db.refresh(user)

        # Check User Quota
        quota_ok, err_msg = check_user_quota(user)
        if not quota_ok:
            raise AppError(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                error_code="PLAN_LIMIT_REACHED",
                message=err_msg
            )

        user_tier = (user.tier or "free").lower()
        max_questions = USER_TIER_MAX_QUESTIONS.get(user_tier, USER_TIER_MAX_QUESTIONS["free"])

        return CallerIdentity(
            kind="user",
            user=user,
            max_questions=max_questions,
            tier=user_tier
        )

    # 3. User via teacher_id form field if present
    if teacher_id and teacher_id.strip():
        user_stmt = select(User).where(User.id == teacher_id.strip())
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if user and user.is_active:
            quota_ok, err_msg = check_user_quota(user)
            if not quota_ok:
                raise AppError(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    error_code="PLAN_LIMIT_REACHED",
                    message=err_msg
                )
            user_tier = (user.tier or "free").lower()
            return CallerIdentity(
                kind="user",
                user=user,
                max_questions=USER_TIER_MAX_QUESTIONS.get(user_tier, USER_TIER_MAX_QUESTIONS["free"]),
                tier=user_tier
            )

    # 4. Unauthenticated Guest
    return CallerIdentity(
        kind="guest",
        max_questions=USER_TIER_MAX_QUESTIONS["guest"],
        tier="guest"
    )

async def deduct_usage(
    identity: CallerIdentity,
    db: AsyncSession,
    questions_generated: int = 0
) -> Dict[str, Any]:
    """
    Deducts 1 generation from the caller's quota pool, adds generated question count,
    persists the change to the database, and checks if the upload hit any limits.
    Returns usage statistics and limit alerts.
    """
    if identity.kind == "user" and identity.user:
        # Re-fetch user to avoid session staleness if needed
        stmt = select(User).where(User.id == identity.user.id)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            user.monthly_generations_used = (user.monthly_generations_used or 0) + 1
            user.monthly_questions_generated = (user.monthly_questions_generated or 0) + max(0, questions_generated)
            await db.commit()
            await db.refresh(user)
            quota_info = get_user_quota_info(user)

            # Check if this upload hit limits
            hit_upload_question_limit = questions_generated >= quota_info["max_questions_per_quiz"]
            hit_monthly_generation_limit = quota_info["generations_remaining"] <= 0
            hit_monthly_question_limit = quota_info["total_questions_remaining"] <= 0
            is_quota_exhausted = quota_info["is_quota_exhausted"]

            limit_hit_warning = None
            if is_quota_exhausted:
                limit_hit_warning = (
                    f"You have reached your monthly generation limit for your {quota_info['tier'].capitalize()} plan. "
                    f"Your quota will renew on {quota_info['renewal_date']}."
                )
            elif hit_upload_question_limit:
                limit_hit_warning = (
                    f"This upload reached the maximum limit of {quota_info['max_questions_per_quiz']} questions per quiz "
                    f"for your {quota_info['tier'].capitalize()} plan."
                )

            return {
                "kind": "user",
                "tier": quota_info["tier"],
                "monthly_generations_used": quota_info["monthly_generations_used"],
                "generations_remaining": quota_info["generations_remaining"],
                "monthly_limit": quota_info["monthly_limit"],
                "monthly_questions_generated": quota_info["monthly_questions_generated"],
                "monthly_questions_limit": quota_info["monthly_questions_limit"],
                "total_questions_remaining": quota_info["total_questions_remaining"],
                "max_questions_per_quiz": quota_info["max_questions_per_quiz"],
                "hit_upload_question_limit": hit_upload_question_limit,
                "hit_monthly_generation_limit": hit_monthly_generation_limit,
                "hit_monthly_question_limit": hit_monthly_question_limit,
                "is_quota_exhausted": is_quota_exhausted,
                "limit_hit_warning": limit_hit_warning,
                "renewal_date": quota_info["renewal_date"]
            }

    elif identity.kind == "tenant" and identity.tenant:
        stmt = select(Tenant).where(Tenant.id == identity.tenant.id)
        res = await db.execute(stmt)
        tenant = res.scalar_one_or_none()
        if tenant:
            tenant.monthly_quota = max(0, (tenant.monthly_quota or 0) - 1)
            await db.commit()
            await db.refresh(tenant)
            return {
                "kind": "tenant",
                "tier": tenant.tier,
                "quota_remaining": tenant.monthly_quota
            }

    return {
        "kind": "guest",
        "tier": "guest",
        "quota_remaining": None
    }
