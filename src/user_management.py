#!/usr/bin/env python3
"""
ZEJZL.NET User Management & Onboarding System
Handles user registration, authentication, trials, and automated conversion
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import secrets

import aiosqlite
from fastapi import HTTPException, APIRouter, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configure logging
logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    FREE_USER = "free_user"
    PRO_USER = "pro_user"
    ENTERPRISE_USER = "enterprise_user"
    ADMIN = "admin"


class OnboardingStep(str, Enum):
    REGISTERED = "registered"
    EMAIL_VERIFIED = "email_verified"
    TRIAL_STARTED = "trial_started"
    TRIAL_ACTIVE = "trial_active"
    TRIAL_EXPIRING = "trial_expiring"
    TRIAL_EXPIRED = "trial_expired"
    CONVERTED = "converted"
    CANCELLED = "cancelled"


@dataclass
class UserProfile:
    id: str
    email: str
    name: str
    role: UserRole
    created_at: datetime
    email_verified: bool = False
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    onboarding_step: OnboardingStep = OnboardingStep.REGISTERED
    api_calls_used: int = 0
    api_calls_limit: Optional[int] = None
    last_login: Optional[datetime] = None
    conversion_triggers: List[str] = None

    def __post_init__(self):
        if self.conversion_triggers is None:
            self.conversion_triggers = []


# Pydantic models for API
class UserRegistration(BaseModel):
    email: EmailStr
    name: str
    password: str
    company: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class EmailVerification(BaseModel):
    token: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    created_at: datetime
    email_verified: bool
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
    onboarding_step: OnboardingStep
    api_calls_used: int
    api_calls_limit: Optional[int]
    days_left_in_trial: Optional[int]
    conversion_progress: float


# Database setup
class UserDatabase:
    """SQLite database for user management"""

    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.algorithm = "HS256"
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'free_user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    email_verified BOOLEAN DEFAULT FALSE,
                    trial_start TIMESTAMP,
                    trial_end TIMESTAMP,
                    subscription_id TEXT,
                    stripe_customer_id TEXT,
                    onboarding_step TEXT DEFAULT 'registered',
                    api_calls_used INTEGER DEFAULT 0,
                    api_calls_limit INTEGER,
                    last_login TIMESTAMP,
                    conversion_triggers TEXT DEFAULT '[]',
                    email_verification_token TEXT,
                    password_reset_token TEXT,
                    password_reset_expires TIMESTAMP,
                    INDEX(email)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    api_calls INTEGER DEFAULT 1,
                    tokens_used INTEGER DEFAULT 0,
                    provider TEXT NOT NULL,
                    cost DECIMAL(10, 4),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversion_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            await db.commit()

    async def create_user(self, user_data: UserRegistration) -> UserProfile:
        """Create new user with email verification"""
        user_id = str(uuid.uuid4())
        password_hash = self.pwd_context.hash(user_data.password)
        verification_token = secrets.token_urlsafe(32)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO users (
                    id, email, name, password_hash, role, 
                    trial_start, trial_end, api_calls_limit,
                    email_verification_token
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    user_data.email,
                    user_data.name,
                    password_hash,
                    UserRole.FREE_USER.value,
                    datetime.now(),
                    datetime.now() + timedelta(days=14),  # 14-day trial
                    1000,  # 1000 API calls during trial
                    verification_token,
                ),
            )
            await db.commit()

        # Create user profile
        user = UserProfile(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            role=UserRole.FREE_USER,
            created_at=datetime.now(),
            trial_start=datetime.now(),
            trial_end=datetime.now() + timedelta(days=14),
            api_calls_limit=1000,
            onboarding_step=OnboardingStep.TRIAL_STARTED,
        )

        await self.log_conversion_event(
            user_id, "trial_started", {"trial_length_days": 14, "api_limit": 1000}
        )

        logger.info(f"Created new user: {user_data.email} with 14-day trial")
        return user, verification_token

    async def verify_email(self, token: str) -> bool:
        """Verify user email"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id FROM users WHERE email_verification_token = ?", (token,)
            )
            user_data = await cursor.fetchone()

            if user_data:
                user_id = user_data[0]
                await db.execute(
                    """
                    UPDATE users SET email_verified = TRUE, onboarding_step = 'trial_active',
                    email_verification_token = NULL WHERE id = ?
                """,
                    (user_id,),
                )
                await db.commit()

                await self.log_conversion_event(user_id, "email_verified")
                logger.info(f"Email verified for user: {user_id}")
                return True

        return False

    async def authenticate_user(
        self, email: str, password: str
    ) -> Optional[UserProfile]:
        """Authenticate user and return profile"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email,))
            user_data = await cursor.fetchone()

            if user_data and self.pwd_context.verify(password, user_data[3]):
                # Update last login
                await db.execute(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (datetime.now(), user_data[0]),
                )
                await db.commit()

                # Convert to UserProfile
                return self._row_to_profile(user_data)

        return None

    async def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user_data = await cursor.fetchone()

            if user_data:
                return self._row_to_profile(user_data)

        return None

    async def update_user_subscription(
        self,
        user_id: str,
        subscription_id: str,
        stripe_customer_id: str,
        role: UserRole,
    ):
        """Update user subscription information"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE users SET 
                subscription_id = ?, stripe_customer_id = ?, role = ?,
                onboarding_step = 'converted', api_calls_limit = NULL
                WHERE id = ?
            """,
                (subscription_id, stripe_customer_id, role.value, user_id),
            )
            await db.commit()

        await self.log_conversion_event(
            user_id,
            "converted",
            {"subscription_id": subscription_id, "role": role.value},
        )

        logger.info(f"User {user_id} converted to {role.value}")

    async def log_api_usage(
        self, user_id: str, api_calls: int, tokens_used: int, provider: str, cost: float
    ):
        """Log API usage for billing"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO usage_logs (user_id, api_calls, tokens_used, provider, cost)
                VALUES (?, ?, ?, ?, ?)
            """,
                (user_id, api_calls, tokens_used, provider, cost),
            )

            # Update user's API call count
            await db.execute(
                """
                UPDATE users SET api_calls_used = api_calls_used + ? WHERE id = ?
            """,
                (api_calls, user_id),
            )
            await db.commit()

    async def log_conversion_event(
        self, user_id: str, event_type: str, event_data: Dict = None
    ):
        """Log conversion funnel events"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO conversion_events (user_id, event_type, event_data)
                VALUES (?, ?, ?)
            """,
                (user_id, event_type, json.dumps(event_data or {})),
            )
            await db.commit()

    async def get_trial_expiring_users(self, days_ahead: int = 3) -> List[UserProfile]:
        """Get users whose trials are expiring soon"""
        cutoff = datetime.now() + timedelta(days=days_ahead)

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT * FROM users 
                WHERE trial_end <= ? AND trial_end > ? AND role = 'free_user'
                AND email_verified = TRUE
            """,
                (cutoff, datetime.now()),
            )

            return [self._row_to_profile(row) for row in await cursor.fetchall()]

    async def get_conversion_analytics(self) -> Dict[str, Any]:
        """Get conversion funnel analytics"""
        async with aiosqlite.connect(self.db_path) as db:
            # Funnel metrics
            cursor = await db.execute("""
                SELECT onboarding_step, COUNT(*) as count 
                FROM users 
                WHERE email_verified = TRUE
                GROUP BY onboarding_step
            """)
            funnel_data = {row[0]: row[1] for row in await cursor.fetchall()}

            # Conversion rate
            cursor = await db.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    SUM(CASE WHEN role != 'free_user' THEN 1 ELSE 0 END) as converted_users
                FROM users WHERE email_verified = TRUE
            """)
            total, converted = await cursor.fetchone()

            conversion_rate = (converted / total * 100) if total > 0 else 0

            # Trial usage
            cursor = await db.execute(
                """
                SELECT AVG(api_calls_used) as avg_usage
                FROM users 
                WHERE trial_end > ? AND role = 'free_user'
            """,
                (datetime.now(),),
            )
            avg_trial_usage = (await cursor.fetchone())[0] or 0

            return {
                "funnel": funnel_data,
                "conversion_rate": round(conversion_rate, 2),
                "total_users": total,
                "converted_users": converted,
                "avg_trial_usage": round(avg_trial_usage, 0),
            }

    def _row_to_profile(self, row) -> UserProfile:
        """Convert database row to UserProfile"""
        # Parse conversion triggers
        triggers = json.loads(row[14]) if row[14] else []

        # Calculate days left in trial
        days_left = None
        if row[6]:  # trial_end
            trial_end = (
                datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6]
            )
            days_left = max(0, (trial_end - datetime.now()).days)

        # Calculate conversion progress (0-100)
        conversion_progress = 0
        if row[12]:  # api_calls_limit
            usage_percent = (row[11] / row[12]) * 100 if row[12] else 0
            time_percent = (
                (
                    (
                        datetime.now()
                        - datetime.fromisoformat(
                            row[5] if isinstance(row[5], str) else row[5].isoformat()
                        )
                    ).days
                    / 14
                )
                * 100
                if row[5]
                else 0
            )
            conversion_progress = min(100, max(usage_percent, time_percent))

        return UserProfile(
            id=row[0],
            email=row[1],
            name=row[2],
            role=UserRole(row[4]),
            created_at=datetime.fromisoformat(row[5])
            if isinstance(row[5], str)
            else row[5],
            email_verified=row[7],
            trial_start=datetime.fromisoformat(row[5])
            if isinstance(row[5], str)
            else row[5],
            trial_end=datetime.fromisoformat(row[6])
            if isinstance(row[6], str)
            else row[6],
            subscription_id=row[8],
            stripe_customer_id=row[9],
            onboarding_step=OnboardingStep(row[10]),
            api_calls_used=row[11],
            api_calls_limit=row[12],
            last_login=datetime.fromisoformat(row[13])
            if row[13] and isinstance(row[13], str)
            else row[13],
            conversion_triggers=triggers,
        )

    def create_access_token(self, user_id: str, expires_delta: timedelta = None):
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)

        to_encode = {"sub": user_id, "exp": expire}
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            return user_id
        except JWTError:
            return None


# Initialize database
user_db = UserDatabase()

# Authentication dependency
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = user_db.verify_token(token)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    user = await user_db.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# Conversion automation
class ConversionAutomation:
    """Automated conversion optimization system"""

    def __init__(self, user_db: UserDatabase):
        self.user_db = user_db
        self.conversion_triggers = {
            "high_usage": 0.7,  # 70% of trial limit used
            "time_expiring": 0.8,  # 80% of trial time elapsed
            "feature_engagement": 3,  # 3+ different features used
        }

    async def check_conversion_triggers(self, user: UserProfile) -> List[str]:
        """Check if user meets conversion triggers"""
        triggers = []

        # High usage trigger
        if (
            user.api_calls_limit
            and user.api_calls_used / user.api_calls_limit
            >= self.conversion_triggers["high_usage"]
        ):
            triggers.append("high_usage")

        # Time expiring trigger
        if user.trial_end:
            time_elapsed = (datetime.now() - user.trial_start).days / 14
            if time_elapsed >= self.conversion_triggers["time_expiring"]:
                triggers.append("time_expiring")

        # Feature engagement trigger (mock - would track actual feature usage)
        if user.api_calls_used >= self.conversion_triggers["feature_engagement"] * 10:
            triggers.append("feature_engagement")

        return triggers

    async def send_conversion_email(self, user: UserProfile, trigger_type: str):
        """Send conversion email based on trigger"""
        # TODO: Implement email service integration
        email_templates = {
            "high_usage": {
                "subject": "⚠️ Running Low on API Calls - Upgrade to Pro",
                "body": f"Hi {user.name}, you've used {user.api_calls_used} of your trial API calls. Upgrade to Pro for unlimited access!",
            },
            "time_expiring": {
                "subject": "⏰ Trial Expiring Soon - Keep Your Access",
                "body": f"Hi {user.name}, your trial expires in {(user.trial_end - datetime.now()).days} days. Upgrade now to maintain access!",
            },
            "trial_expired": {
                "subject": "🔒 Trial Expired - Reactivate Your Account",
                "body": f"Hi {user.name}, your trial has expired. Subscribe to Pro to continue using zejzl.net!",
            },
        }

        template = email_templates.get(trigger_type, email_templates["trial_expired"])

        await self.user_db.log_conversion_event(
            user.id,
            f"conversion_email_sent_{trigger_type}",
            {"trigger": trigger_type, "subject": template["subject"]},
        )

        logger.info(f"Conversion email sent to {user.email}: {trigger_type}")

    async def process_trial_expiration(self):
        """Process users with expiring trials"""
        expiring_users = await self.user_db.get_trial_expiring_users(3)

        for user in expiring_users:
            triggers = await self.check_conversion_triggers(user)

            # Send appropriate conversion emails
            if "high_usage" in triggers or "time_expiring" in triggers:
                await self.send_conversion_email(user, "time_expiring")

            # Check if trial expired
            if user.trial_end and user.trial_end <= datetime.now():
                await self.send_conversion_email(user, "trial_expired")


# Initialize conversion automation
conversion_automation = ConversionAutomation(user_db)

# FastAPI router
onboarding_router = APIRouter(prefix="/api/auth", tags=["authentication"])


@onboarding_router.post("/register")
async def register_user(user_data: UserRegistration):
    """Register new user with 14-day trial"""
    try:
        await user_db.initialize()
        user, verification_token = await user_db.create_user(user_data)

        # TODO: Send verification email
        logger.info(
            f"User registered: {user_data.email}, verification token: {verification_token}"
        )

        return {
            "success": True,
            "message": "Registration successful! Please check your email to verify your account.",
            "user_id": user.id,
            "trial_days": 14,
        }

    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@onboarding_router.post("/verify-email")
async def verify_email(request: EmailVerification):
    """Verify user email"""
    try:
        success = await user_db.verify_email(request.token)

        if success:
            return {"success": True, "message": "Email verified! You can now login."}
        else:
            raise HTTPException(status_code=400, detail="Invalid verification token")

    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@onboarding_router.post("/login")
async def login_user(credentials: UserLogin):
    """Authenticate user and return token"""
    try:
        user = await user_db.authenticate_user(credentials.email, credentials.password)

        if user:
            if not user.email_verified:
                raise HTTPException(
                    status_code=401, detail="Please verify your email first"
                )

            access_token = user_db.create_access_token(user.id)

            return {
                "success": True,
                "access_token": access_token,
                "token_type": "bearer",
                "user": UserProfileResponse(
                    **asdict(user),
                    days_left_in_trial=(user.trial_end - datetime.now()).days
                    if user.trial_end
                    else None,
                    conversion_progress=75.0,  # Mock calculation
                ).dict(),
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@onboarding_router.get("/profile")
async def get_user_profile(current_user: UserProfile = Depends(get_current_user)):
    """Get current user profile"""
    days_left = (
        (current_user.trial_end - datetime.now()).days
        if current_user.trial_end
        else None
    )

    return UserProfileResponse(
        **asdict(current_user),
        days_left_in_trial=days_left,
        conversion_progress=75.0,  # Mock calculation
    )


@onboarding_router.get("/analytics")
async def get_onboarding_analytics():
    """Get conversion funnel analytics"""
    try:
        analytics = await user_db.get_conversion_analytics()
        return {"success": True, "data": analytics}
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@onboarding_router.post("/trigger-conversion-check")
async def trigger_conversion_check(
    current_user: UserProfile = Depends(get_current_user),
):
    """Manually trigger conversion check for current user"""
    try:
        triggers = await conversion_automation.check_conversion_triggers(current_user)

        for trigger in triggers:
            await conversion_automation.send_conversion_email(current_user, trigger)

        return {
            "success": True,
            "triggers_found": triggers,
            "message": f"Conversion emails sent for: {', '.join(triggers)}",
        }
    except Exception as e:
        logger.error(f"Conversion trigger error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
