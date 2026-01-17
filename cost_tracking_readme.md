# Cost Tracking & Analytics Documentation

## Overview

ZEJZL.NET Phase 7 introduces comprehensive cost tracking and token usage analytics to help monitor and optimize AI provider usage costs.

## Features

### 1. Real-time Token Counting
- Automatic token counting for all AI provider responses
- Support for prompt tokens, completion tokens, and total tokens
- Compatible with OpenAI, Claude, Gemini, and other providers

### 2. Cost Calculation Engine
- Automatic cost calculation based on provider pricing models
- Support for different pricing tiers and models
- Real-time cost updates for each request

### 3. Analytics Dashboard
Web-based analytics available at:
- `/api/analytics/usage` - General usage statistics
- `/api/analytics/costs` - Cost analysis and trends
- `/api/analytics/provider/{provider}` - Provider-specific analytics
- `/api/analytics/expensive-requests` - Most expensive individual requests

### 4. Database Schema
Enhanced SQLite schema with analytics tables:
- `daily_usage` - Daily aggregated statistics
- `provider_usage` - Per-provider, per-model usage data
- `hourly_usage` - Hourly usage patterns
- Extended `messages` table with token and cost columns

## API Endpoints

### Usage Analytics
```bash
GET /api/analytics/usage?days=7
```
Returns comprehensive usage report including requests, tokens, costs, and provider breakdown.

### Cost Analysis
```bash
GET /api/analytics/costs?days=30
```
Provides cost analysis with trends, projections, and optimization insights.

### Provider Performance
```bash
GET /api/analytics/provider/{provider}?days=7
```
Detailed performance metrics for a specific AI provider.

### Expensive Requests
```bash
GET /api/analytics/expensive-requests?limit=10
```
Lists the most expensive individual API requests.

## Pricing Models

The system includes built-in pricing models for major AI providers:

### OpenAI (ChatGPT)
- GPT-3.5-turbo: $0.0015 input / $0.002 output per 1K tokens
- GPT-4: $0.03 input / $0.06 output per 1K tokens
- GPT-4-turbo: $0.01 input / $0.03 output per 1K tokens

### Anthropic (Claude)
- Claude 3 Opus: $0.015 input / $0.075 output per 1K tokens
- Claude 3 Sonnet: $0.003 input / $0.015 output per 1K tokens
- Claude 3.5 Sonnet: $0.003 input / $0.015 output per 1K tokens

### Google (Gemini)
- Gemini Pro: $0.00025 input / $0.0005 output per 1K tokens

## Usage Examples

### Python API Usage
```python
from src.usage_analytics import UsageAnalytics

analytics = UsageAnalytics()

# Get usage report for last 7 days
report = await analytics.get_usage_report(days=7)
print(f"Total cost: ${report.total_cost_usd}")
print(f"Total tokens: {report.total_tokens}")

# Get cost analysis
cost_analysis = await analytics.get_cost_analysis(days=30)
print(f"Projected monthly cost: ${cost_analysis.projected_monthly_cost}")

# Get provider performance
claude_perf = await analytics.get_provider_performance("Claude", days=7)
print(f"Claude success rate: {claude_perf['success_rate']:.1%}")
```

### Web Dashboard
Access the analytics dashboard at `http://localhost:8000` and navigate to the analytics section, or use the API endpoints directly.

## Database Migration

The system includes automatic database schema migration to add cost tracking columns to existing installations without data loss.

## Configuration

No additional configuration is required. Cost tracking is automatically enabled for all AI provider interactions.

## Future Enhancements

- Cost optimization recommendations
- Budget alerts and limits
- Token usage forecasting
- Provider comparison analytics
- Cost trend analysis with machine learning</content>
<parameter name="filePath">zejzl_net/COST_TRACKING_README.md