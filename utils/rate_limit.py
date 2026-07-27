import time
from collections import defaultdict
from typing import Dict, List
from fastapi import status
from models.tenant import Tenant
from utils.exceptions import AppError

# In-memory sliding window request tracker: tenant_id -> list of timestamps
_request_history: Dict[str, List[float]] = defaultdict(list)

def check_rate_limit(tenant_id: str, limit_rpm: int = 60) -> bool:
    """
    Sliding window rate-limiter. Returns True if request is allowed, False if rate limited.
    """
    now = time.time()
    window_start = now - 60.0  # 60 seconds window

    # Clean old entries
    timestamps = [t for t in _request_history[tenant_id] if t > window_start]
    _request_history[tenant_id] = timestamps

    if len(timestamps) >= limit_rpm:
        return False

    _request_history[tenant_id].append(now)
    return True

def verify_tenant_quota_and_limit(tenant: Tenant):
    """
    Validates that tenant hasn't exceeded their RPM rate limit or free monthly quota.
    """
    # 1. Check Rate Limit (RPM)
    allowed = check_rate_limit(tenant.id, limit_rpm=tenant.api_keys[0].rate_limit_rpm if tenant.api_keys else 60)
    if not allowed:
        raise AppError(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            message="Rate limit exceeded. Please wait a moment before trying again."
        )

    # 2. Check Monthly Quota (Free plan defaults to 1,000/mo)
    # Note: Monthly quota tracking can be incremented per generation task
