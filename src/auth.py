"""
Authentication and Authorization for ZEJZL.NET API
Provides API key-based authentication and rate limiting
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import Security, HTTPException, status, Depends, Request
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# API Key authentication (primary method)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Bearer token authentication (alternative method)
bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
    """Custom exception for authentication failures"""
    pass


class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
        self.limits = {
            "free": 10,  # 10 requests per minute
            "pro": 100,  # 100 requests per minute
            "enterprise": 1000,  # 1000 requests per minute
        }
    
    def check_rate_limit(self, api_key: str, tier: str = "free") -> bool:
        """Check if request is within rate limit"""
        now = datetime.now()
        window_start = now - timedelta(minutes=1)
        
        # Clean old requests
        if api_key in self.requests:
            self.requests[api_key] = [
                req_time for req_time in self.requests[api_key]
                if req_time > window_start
            ]
        else:
            self.requests[api_key] = []
        
        # Check limit
        limit = self.limits.get(tier, self.limits["free"])
        if len(self.requests[api_key]) >= limit:
            return False
        
        # Add current request
        self.requests[api_key].append(now)
        return True
    
    def get_remaining(self, api_key: str, tier: str = "free") -> int:
        """Get remaining requests in current window"""
        now = datetime.now()
        window_start = now - timedelta(minutes=1)
        
        if api_key not in self.requests:
            return self.limits.get(tier, self.limits["free"])
        
        recent = [
            req_time for req_time in self.requests[api_key]
            if req_time > window_start
        ]
        limit = self.limits.get(tier, self.limits["free"])
        return max(0, limit - len(recent))


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_valid_api_keys() -> Dict[str, Dict[str, str]]:
    """
    Load valid API keys from environment variables
    
    Format: API_KEY_1=key1:tier:description, API_KEY_2=key2:tier:description
    
    Returns dict: {key_hash: {key, tier, description}}
    """
    keys = {}
    
    # Load from environment variables
    for env_key, env_value in os.environ.items():
        if env_key.startswith("ZEJZL_API_KEY_"):
            try:
                # Parse format: "actual_key:tier:description"
                parts = env_value.split(":", 2)
                if len(parts) >= 2:
                    api_key = parts[0]
                    tier = parts[1] if len(parts) > 1 else "free"
                    description = parts[2] if len(parts) > 2 else "API Key"
                    
                    # Hash the key for storage (security)
                    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                    
                    keys[key_hash] = {
                        "key": api_key,
                        "tier": tier,
                        "description": description
                    }
            except Exception as e:
                logger.error(f"Failed to parse API key {env_key}: {e}")
    
    # If no keys configured, log warning
    if not keys:
        logger.warning(
            "⚠️ No API keys configured! "
            "Set ZEJZL_API_KEY_1=your_key:tier:description in .env"
        )
        
        # For development, create a default key
        if os.getenv("ENVIRONMENT", "production") == "development":
            dev_key = "dev_test_key_insecure"
            key_hash = hashlib.sha256(dev_key.encode()).hexdigest()
            keys[key_hash] = {
                "key": dev_key,
                "tier": "pro",
                "description": "Development Test Key"
            }
            logger.info("🔓 Development mode: Using insecure test key")
    
    return keys


def verify_api_key(api_key: str) -> Optional[Dict[str, str]]:
    """
    Verify API key and return key info
    
    Returns None if invalid, or dict with {tier, description}
    """
    if not api_key:
        return None
    
    valid_keys = get_valid_api_keys()
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    if key_hash in valid_keys:
        key_info = valid_keys[key_hash]
        return {
            "tier": key_info["tier"],
            "description": key_info["description"]
        }
    
    return None


async def get_api_key_from_header(
    api_key_header: Optional[str] = Security(api_key_header),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> str:
    """
    Extract API key from request headers
    
    Supports two formats:
    1. X-API-Key: your_key
    2. Authorization: Bearer your_key
    """
    # Try X-API-Key header first
    if api_key_header:
        return api_key_header
    
    # Try Authorization: Bearer header
    if bearer_token:
        return bearer_token.credentials
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No API key provided. Include X-API-Key header or Authorization: Bearer token.",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def authenticate(
    request: Request,
    api_key: str = Depends(get_api_key_from_header)
) -> Dict[str, str]:
    """
    Authenticate request using API key
    
    Returns key info dict or raises HTTPException
    """
    # Verify the key
    key_info = verify_api_key(api_key)
    if not key_info:
        logger.warning(f"Invalid API key attempted from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check rate limit
    if not rate_limiter.check_rate_limit(api_key, key_info["tier"]):
        remaining = rate_limiter.get_remaining(api_key, key_info["tier"])
        logger.warning(
            f"Rate limit exceeded for key {key_info['description']} "
            f"from {request.client.host}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in 60 seconds.",
            headers={
                "X-RateLimit-Remaining": str(remaining),
                "Retry-After": "60"
            }
        )
    
    # Log successful authentication
    logger.info(
        f"✓ Authenticated: {key_info['description']} "
        f"(tier: {key_info['tier']}) from {request.client.host}"
    )
    
    # Add rate limit headers to response
    remaining = rate_limiter.get_remaining(api_key, key_info["tier"])
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_tier = key_info["tier"]
    
    return key_info


def optional_authenticate(
    request: Request,
    api_key_header: Optional[str] = Security(api_key_header),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Optional[Dict[str, str]]:
    """
    Optional authentication - allows both authenticated and anonymous access
    
    Returns key info if authenticated, None if anonymous
    """
    # Try to get API key
    api_key = None
    if api_key_header:
        api_key = api_key_header
    elif bearer_token:
        api_key = bearer_token.credentials
    
    if not api_key:
        return None
    
    # Verify key if provided
    key_info = verify_api_key(api_key)
    if key_info:
        # Check rate limit
        if not rate_limiter.check_rate_limit(api_key, key_info["tier"]):
            # For optional auth, don't block - just treat as anonymous
            logger.warning(f"Rate limit exceeded for optional auth: {key_info['description']}")
            return None
        
        logger.info(f"✓ Optional auth: {key_info['description']}")
        return key_info
    
    return None


def generate_api_key(prefix: str = "zejzl") -> str:
    """
    Generate a secure random API key
    
    Format: zejzl_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx (40 chars total)
    """
    random_part = secrets.token_urlsafe(24)  # 32 chars base64
    return f"{prefix}_{random_part}"


# Dependency shortcuts
RequireAuth = Depends(authenticate)
OptionalAuth = Depends(optional_authenticate)
