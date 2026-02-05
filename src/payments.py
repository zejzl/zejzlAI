#!/usr/bin/env python3
"""
ZEJZL.NET Payment Processing System
Handles Stripe integration, subscription management, and billing
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import stripe
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class SubscriptionPlan:
    name: str
    price_id: Optional[str]
    amount: int  # in cents
    currency: str = "usd"
    interval: str = "month"
    features: List[str] = None
    api_calls_limit: Optional[int] = None
    model_access: List[str] = None


# Subscription plans configuration
SUBSCRIPTION_PLANS = {
    SubscriptionTier.FREE: SubscriptionPlan(
        name="Free Tier",
        price_id=None,
        amount=0,
        features=[
            "Basic framework access",
            "1,000 API calls/month",
            "Community support",
            "Access to: ChatGPT, Claude",
        ],
        api_calls_limit=1000,
        model_access=["chatgpt", "claude"],
    ),
    SubscriptionTier.PRO: SubscriptionPlan(
        name="Pro Tier",
        price_id="price_1OLtdsLkdFw6L2VvFjXmNqbL",  # Will be set in Stripe
        amount=2900,  # $29.00
        features=[
            "Unlimited API calls",
            "All 7 AI providers",
            "Priority support",
            "Advanced features",
            "Custom agents",
            "API analytics",
        ],
        api_calls_limit=None,
        model_access=["chatgpt", "claude", "gemini", "grok", "deepseek", "qwen", "zai"],
    ),
    SubscriptionTier.ENTERPRISE: SubscriptionPlan(
        name="Enterprise Tier",
        price_id="price_1OLtdsLkdFw6L2VvFjXmNqbL",  # Will be set in Stripe
        amount=29900,  # $299.00
        interval="month",
        features=[
            "Unlimited everything",
            "Custom model fine-tuning",
            "White-label options",
            "Dedicated support",
            "SLA guarantee",
            "On-premise deployment",
        ],
        api_calls_limit=None,
        model_access=["chatgpt", "claude", "gemini", "grok", "deepseek", "qwen", "zai"],
    ),
}


# Pydantic models for API
class CreateCheckoutSessionRequest(BaseModel):
    tier: SubscriptionTier
    user_id: str
    success_url: str = "https://zejzl.net/success"
    cancel_url: str = "https://zejzl.net/pricing"


class CustomerPortalRequest(BaseModel):
    customer_id: str
    return_url: str = "https://zejzl.net/billing"


class SubscriptionResponse(BaseModel):
    subscription_id: str
    customer_id: str
    tier: SubscriptionTier
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    api_calls_used: int = 0
    api_calls_limit: Optional[int] = None


class PaymentManager:
    """Manages all payment processing and subscription logic"""

    def __init__(self):
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if not self.stripe_api_key:
            logger.warning("STRIPE_API_KEY not configured - payment system disabled")
            self.enabled = False
        else:
            stripe.api_key = self.stripe_api_key
            self.enabled = True
            logger.info("Payment system initialized with Stripe")

    async def create_checkout_session(
        self, request: CreateCheckoutSessionRequest
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription"""
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Payment system not available")

        plan = SUBSCRIPTION_PLANS[request.tier]

        try:
            # Create or retrieve customer
            customer = await self._get_or_create_customer(request.user_id)

            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": plan.price_id,
                        "quantity": 1,
                    }
                ]
                if plan.price_id
                else [
                    {
                        "price_data": {
                            "currency": plan.currency,
                            "unit_amount": plan.amount,
                            "product_data": {
                                "name": plan.name,
                                "description": ", ".join(plan.features[:3]),
                            },
                            "recurring": {
                                "interval": plan.interval,
                            },
                        },
                        "quantity": 1,
                    }
                ],
                mode="subscription" if plan.amount > 0 else "payment",
                success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=request.cancel_url,
                metadata={"user_id": request.user_id, "tier": request.tier.value},
            )

            logger.info(
                f"Created checkout session {checkout_session.id} for user {request.user_id}"
            )
            return {"url": checkout_session.url}

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def _get_or_create_customer(self, user_id: str) -> stripe.Customer:
        """Get existing customer or create new one"""
        try:
            # Search for existing customer
            customers = stripe.Customer.list(
                email=f"user_{user_id}@zejzl.net"
            ).auto_paging_iter()
            for customer in customers:
                if customer.metadata.get("user_id") == user_id:
                    return customer
        except Exception as e:
            logger.warning(f"Error searching for customer: {e}")

        # Create new customer
        customer = stripe.Customer.create(
            email=f"user_{user_id}@zejzl.net",
            metadata={"user_id": user_id},
            name=f"User {user_id}",
        )
        logger.info(f"Created new customer {customer.id} for user {user_id}")
        return customer

    async def create_customer_portal_session(
        self, request: CustomerPortalRequest
    ) -> Dict[str, Any]:
        """Create Stripe Customer Portal session for billing management"""
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Payment system not available")

        try:
            session = stripe.billing_portal.Session.create(
                customer=request.customer_id,
                return_url=request.return_url,
            )
            return {"url": session.url}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def get_subscription(self, subscription_id: str) -> SubscriptionResponse:
        """Get subscription details"""
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Payment system not available")

        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            customer = stripe.Customer.retrieve(sub.customer)

            # Determine tier from price
            tier = SubscriptionTier.FREE
            if sub.items.data:
                price_id = sub.items.data[0].price.id
                for plan_tier, plan in SUBSCRIPTION_PLANS.items():
                    if plan.price_id == price_id:
                        tier = plan_tier
                        break

            return SubscriptionResponse(
                subscription_id=sub.id,
                customer_id=sub.customer,
                tier=tier,
                status=sub.status,
                current_period_start=datetime.fromtimestamp(sub.current_period_start),
                current_period_end=datetime.fromtimestamp(sub.current_period_end),
                cancel_at_period_end=sub.cancel_at_period_end,
                api_calls_limit=SUBSCRIPTION_PLANS[tier].api_calls_limit,
            )
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving subscription: {e}")
            raise HTTPException(status_code=404, detail="Subscription not found")

    async def cancel_subscription(
        self, subscription_id: str, immediate: bool = False
    ) -> Dict[str, Any]:
        """Cancel subscription (immediate or at period end)"""
        if not self.enabled:
            raise HTTPException(status_code=503, detail="Payment system not available")

        try:
            if immediate:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id, cancel_at_period_end=True
                )

            logger.info(
                f"Cancelled subscription {subscription_id} (immediate: {immediate})"
            )
            return {"status": subscription.status, "cancelled": True}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def handle_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """Process Stripe webhook events"""
        if not self.enabled:
            logger.warning("Payment system disabled - ignoring webhook")
            return {"status": "ignored"}

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle different event types
        event_handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
            "customer.subscription.deleted": self._handle_subscription_cancelled,
            "customer.subscription.updated": self._handle_subscription_updated,
        }

        handler = event_handlers.get(event.type)
        if handler:
            await handler(event.data.object)
        else:
            logger.info(f"Unhandled webhook event type: {event.type}")

        return {"status": "processed", "type": event.type}

    async def _handle_checkout_completed(self, session: stripe.checkout.Session):
        """Handle successful checkout"""
        user_id = session.metadata.get("user_id")
        tier = session.metadata.get("tier")

        logger.info(f"Checkout completed for user {user_id}, tier {tier}")

        # TODO: Update user's subscription in database
        # TODO: Send welcome email
        # TODO: Grant access to premium features

    async def _handle_payment_succeeded(self, invoice: stripe.Invoice):
        """Handle successful payment"""
        logger.info(f"Payment succeeded for subscription {invoice.subscription}")

        # TODO: Update subscription status in database
        # TODO: Send payment confirmation
        # TODO: Reset API call counter if applicable

    async def _handle_payment_failed(self, invoice: stripe.Invoice):
        """Handle failed payment"""
        logger.warning(f"Payment failed for subscription {invoice.subscription}")

        # TODO: Notify user of payment failure
        # TODO: Update subscription status in database
        # TODO: Schedule retry or downgrade

    async def _handle_subscription_cancelled(self, subscription: stripe.Subscription):
        """Handle subscription cancellation"""
        logger.info(f"Subscription cancelled: {subscription.id}")

        # TODO: Update user's subscription in database
        # TODO: Revoke premium access
        # TODO: Send cancellation confirmation

    async def _handle_subscription_updated(self, subscription: stripe.Subscription):
        """Handle subscription updates"""
        logger.info(f"Subscription updated: {subscription.id}")

        # TODO: Update user's subscription in database
        # TODO: Adjust feature access accordingly

    def get_plans(self) -> Dict[str, Any]:
        """Get all available subscription plans"""
        return {
            tier.value: {
                "name": plan.name,
                "amount": plan.amount,
                "currency": plan.currency,
                "interval": plan.interval,
                "features": plan.features,
                "api_calls_limit": plan.api_calls_limit,
                "model_access": plan.model_access,
            }
            for tier, plan in SUBSCRIPTION_PLANS.items()
        }


# Initialize payment manager
payment_manager = PaymentManager()

# FastAPI router
payment_router = APIRouter(prefix="/api/payments", tags=["payments"])


@payment_router.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    return payment_manager.get_plans()


@payment_router.post("/checkout")
async def create_checkout_session(request: CreateCheckoutSessionRequest):
    """Create checkout session for subscription"""
    return await payment_manager.create_checkout_session(request)


@payment_router.post("/portal")
async def create_customer_portal_session(request: CustomerPortalRequest):
    """Create customer portal session for billing management"""
    return await payment_manager.create_customer_portal_session(request)


@payment_router.get("/subscription/{subscription_id}")
async def get_subscription(subscription_id: str):
    """Get subscription details"""
    return await payment_manager.get_subscription(subscription_id)


@payment_router.delete("/subscription/{subscription_id}")
async def cancel_subscription(subscription_id: str, immediate: bool = False):
    """Cancel subscription"""
    return await payment_manager.cancel_subscription(subscription_id, immediate)


@payment_router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    return await payment_manager.handle_webhook(payload.decode(), sig_header)
