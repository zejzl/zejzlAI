# Budget Alert System

## Overview

Automatic Discord notifications for token budget monitoring. Prevents runaway costs by alerting at 80%, 90%, and 100% usage thresholds.

## Features

### Three-Tier Alert System
- **⚠️ WARNING (80%)** - Yellow alert when budget hits 80%
- **🚨 CRITICAL (90%)** - Red alert when budget hits 90%
- **🛑 EXHAUSTED (100%)** - Black alert when budget exhausted + block new requests

### Smart Deduplication
- Only sends each alert level once per task
- Prevents notification spam
- Tracks alert history in `budget_alerts.json`

### Rich Discord Embeds
- Color-coded by severity (yellow/red/black)
- Shows tokens used, remaining, percentage
- Includes dashboard link for quick access
- Timestamp and action recommendations

## Setup

### 1. Create Discord Webhook

1. Go to your Discord server settings
2. Navigate to Integrations → Webhooks
3. Click "New Webhook"
4. Copy the webhook URL

### 2. Configure Environment Variable

Add to `.env`:
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
```

### 3. Restart Server

```bash
cd C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net
python web_dashboard.py
```

## Testing

### Test Alert Endpoint

Send a POST request to trigger a test alert:

```bash
curl -X POST http://localhost:8000/api/swarm/test-alert \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test_alert",
    "tokens_used": 8500,
    "budget_limit": 10000
  }'
```

**Expected Discord notification:**
- 85% usage → WARNING alert
- Yellow embed with usage stats
- Link to dashboard

### Test Different Thresholds

**WARNING (80%):**
```json
{
  "tokens_used": 8000,
  "budget_limit": 10000
}
```

**CRITICAL (90%):**
```json
{
  "tokens_used": 9200,
  "budget_limit": 10000
}
```

**EXHAUSTED (100%):**
```json
{
  "tokens_used": 10500,
  "budget_limit": 10000
}
```

## Usage

### Automatic Alerts

Alerts trigger automatically when tasks spend tokens:

```python
# When you use the /api/chat-swarm endpoint
result = await swarm.process_task(
    task="Deploy database update",
    budget=10000  # Budget limit
)

# If task uses 8000+ tokens → WARNING alert sent
# If task uses 9000+ tokens → CRITICAL alert sent
# If task uses 10000+ tokens → EXHAUSTED alert sent
```

### Manual Alert Check

```python
from src.budget_alerts import send_budget_alert

result = await send_budget_alert(
    task_id="task_123",
    tokens_used=8500,
    budget_limit=10000
)

if result["alert_sent"]:
    print(f"Alert sent: {result['alert_level']}")
```

## Alert Data

### Alert History File

Location: `skills/swarm-orchestrator/data/budget_alerts.json`

```json
{
  "alerts_sent": {
    "task_123": ["WARNING", "CRITICAL"],
    "task_456": ["WARNING"]
  },
  "total_alerts": 3,
  "last_alert": "2026-02-05T14:15:00Z"
}
```

### Discord Embed Format

```
⚠️ Budget Alert: WARNING

Task **task_123** has reached 85.0% of budget

Tokens Used: 8,500
Budget Limit: 10,000
Remaining: 1,500
Percentage: 85.0%
Status: WARNING
Dashboard: [View Dashboard](http://localhost:8000/blackboard)

⚠️ Action Recommended
Budget approaching limit - monitor task progress
```

## Integration Points

### 1. SwarmCoordinator

Budget alerts automatically trigger in `BudgetTracker.spend()`:

```python
# In src/swarm_wrapper.py
def spend(self, task_id: str, tokens: int, reason: str):
    # ... update budget ...
    
    # Trigger alert (async, non-blocking)
    if self.alert_manager:
        asyncio.create_task(
            self.alert_manager.check_and_notify(
                task_id,
                budget["used_tokens"],
                budget["max_tokens"]
            )
        )
```

### 2. Web Dashboard

Test endpoint: `POST /api/swarm/test-alert`

Returns:
```json
{
  "success": true,
  "result": {
    "task_id": "test_task",
    "tokens_used": 8500,
    "budget_limit": 10000,
    "percentage": 85.0,
    "alert_level": "WARNING",
    "alert_sent": true
  },
  "message": "Alert check complete: WARNING"
}
```

## Thresholds

| Level | Percentage | Status | Color | Action |
|-------|-----------|--------|-------|--------|
| OK | 0-79% | Normal | Green | Monitor |
| WARNING | 80-89% | Caution | Yellow | Watch closely |
| CRITICAL | 90-99% | Urgent | Red | Consider action |
| EXHAUSTED | 100%+ | Blocked | Black | Increase budget |

## Best Practices

### 1. Set Appropriate Budgets
- Small tasks: 2,500 tokens
- Standard tasks: 10,000 tokens
- Large tasks: 25,000 tokens
- Research tasks: 50,000 tokens

### 2. Monitor Alerts
- Check Discord for warning alerts
- Investigate high-usage tasks
- Adjust budgets based on patterns

### 3. Alert Fatigue Prevention
- Alerts only sent once per threshold per task
- No spam from repeated checks
- Historical tracking for analysis

### 4. Quick Response
- WARNING → Monitor progress
- CRITICAL → Review task, consider stopping
- EXHAUSTED → Investigate cause, adjust budget

## Troubleshooting

### No Alerts Received

**Check webhook URL:**
```bash
# Verify .env contains correct webhook
cat .env | grep DISCORD_WEBHOOK_URL
```

**Test webhook manually:**
```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message"}'
```

### Alerts Not Triggering

**Check alert manager initialization:**
```python
# In Python console
from src.budget_alerts import BudgetAlertManager
manager = BudgetAlertManager()
print(manager.webhook_url)  # Should show your webhook URL
```

**Check alert history:**
```bash
cat skills/swarm-orchestrator/data/budget_alerts.json
```

### Alert Spam

Alerts should only send once per threshold per task. If you're getting spam:

1. Check `budget_alerts.json` for duplicate task IDs
2. Verify deduplication logic in `should_send_alert()`
3. Clear alert history if needed:
   ```bash
   rm skills/swarm-orchestrator/data/budget_alerts.json
   ```

## Future Enhancements

- [ ] Email alerts (for non-Discord users)
- [ ] Slack integration
- [ ] Custom threshold configuration per task
- [ ] Daily/weekly budget summary reports
- [ ] Cost projection alerts ("at current rate, will exceed budget in 2 hours")
- [ ] Multi-channel alerts (Discord + email + SMS)

---

**Created:** February 5, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅
