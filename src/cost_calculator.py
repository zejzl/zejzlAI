"""
Cost Calculator for AI Provider Token Usage
Calculates costs in USD based on provider pricing models and token usage.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TokenUsage:
    """Token usage tracking for AI provider responses"""
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


class CostCalculator:
    """Calculates costs for AI provider usage based on token consumption"""

    # Pricing data (USD per 1K tokens) - Update these with current rates
    PRICING = {
        "chatgpt": {
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},  # $1.50/$2.00 per 1K tokens
            "gpt-4": {"input": 0.03, "output": 0.06},            # $30/$60 per 1K tokens
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},      # $10/$30 per 1K tokens
        },
        "claude": {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},     # $15/$75 per 1K tokens
            "claude-3-opus-20240229": {"input": 0.003, "output": 0.015},  # $3/$15 per 1K tokens
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}, # $0.25/$1.25 per 1K tokens
            "claude-3-opus-20240229": {"input": 0.003, "output": 0.015}, # $3/$15 per 1K tokens
        },
        "gemini": {
            "gemini-2.5-flash": {"input": 0.00015, "output": 0.0006},    # $0.15/$0.60 per 1K tokens (actually per 1M)
            "gemini-2.5-pro": {"input": 0.00125, "output": 0.005},       # $1.25/$5.00 per 1K tokens (actually per 1M)
            "gemini-3-pro-preview": {"input": 0.0025, "output": 0.01},   # Estimated pricing
        },
        "grok": {
            "grok-1": {"input": 0.005, "output": 0.015},  # Estimated pricing
        },
        # Placeholder pricing for other providers
        "zai": {"zai-1": {"input": 0.01, "output": 0.02}},
        "deepseek": {"deepseek-coder": {"input": 0.001, "output": 0.002}},
        "qwen": {"qwen-turbo": {"input": 0.0015, "output": 0.002}},
    }

    @classmethod
    def calculate_cost(cls, token_usage: TokenUsage) -> float:
        """
        Calculate cost in USD for the given token usage

        Args:
            token_usage: TokenUsage object with provider, model, and token counts

        Returns:
            Cost in USD (float)
        """
        provider = token_usage.provider.lower()
        model = token_usage.model.lower()

        # Get pricing for this provider/model
        provider_pricing = cls.PRICING.get(provider, {})
        model_pricing = provider_pricing.get(model, {})

        # If no specific pricing found, use default
        if not model_pricing:
            # Try to find a matching model or use first available
            for model_key, pricing in provider_pricing.items():
                if model_key in model or model in model_key:
                    model_pricing = pricing
                    break
            else:
                # Use first available pricing or default
                model_pricing = next(iter(provider_pricing.values()), {"input": 0.01, "output": 0.02})

        # Calculate costs
        input_cost = (token_usage.prompt_tokens / 1000) * model_pricing.get("input", 0.01)
        output_cost = (token_usage.completion_tokens / 1000) * model_pricing.get("output", 0.02)

        total_cost = input_cost + output_cost

        # Update the token_usage object with calculated cost
        token_usage.cost_usd = round(total_cost, 6)  # Round to 6 decimal places

        return token_usage.cost_usd

    @classmethod
    def get_provider_pricing(cls, provider: str, model: str) -> Dict[str, float]:
        """
        Get pricing information for a specific provider and model

        Args:
            provider: Provider name (case insensitive)
            model: Model name (case insensitive)

        Returns:
            Dict with 'input' and 'output' pricing per 1K tokens
        """
        provider = provider.lower()
        model = model.lower()

        provider_pricing = cls.PRICING.get(provider, {})
        model_pricing = provider_pricing.get(model, {})

        if not model_pricing:
            # Try partial matching
            for model_key, pricing in provider_pricing.items():
                if model_key in model or model in model_key:
                    return pricing

        return model_pricing if model_pricing else {"input": 0.01, "output": 0.02}

    @classmethod
    def estimate_cost(cls, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost for a hypothetical usage scenario

        Args:
            provider: Provider name
            model: Model name
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        token_usage = TokenUsage(
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        return cls.calculate_cost(token_usage)