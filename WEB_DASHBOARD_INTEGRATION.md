# Web Dashboard Integration - Pantheon Swarm

**Date:** February 5, 2026  
**Status:** ✅ Integrated & Ready to Test  
**File:** `web_dashboard.py`

---

## ✅ What Was Added

### 1. Import PantheonSwarm

```python
# Import Pantheon Swarm
try:
    from pantheon_swarm import PantheonSwarm, BudgetExhaustedError, PermissionDeniedError
except ImportError:
    PantheonSwarm = None
    logger.warning("PantheonSwarm not available - swarm features disabled")
```

### 2. Initialize in DashboardServer

```python
class DashboardServer:
    def __init__(self):
        # ... existing code ...
        self.swarm: PantheonSwarm = None
    
    async def _initialize_swarm(self):
        """Initialize Pantheon Swarm for budget-tracked multi-agent coordination"""
        if PantheonSwarm:
            self.swarm = PantheonSwarm(
                pantheon_config_path="pantheon_config.json",
                model="grok-4-fast-reasoning",
                verbose=False
            )
            logger.info("✓ Pantheon Swarm initialized")
```

### 3. New API Endpoints

**POST /api/chat-swarm** - Main chat endpoint with swarm coordination
- Auto-detects required permissions from message
- Tracks budget usage
- Returns detailed status

**GET /api/swarm/budget/{task_id}** - Get budget status for a task

**GET /api/swarm/blackboard** - Get all blackboard state

**GET /api/swarm/blackboard/{key}** - Get specific blackboard key

---

## 📊 API Usage

### Send Message with Swarm

```javascript
POST /api/chat-swarm
{
  "message": "Deploy new chat feature to production",
  "budget": 15000,  // Optional, defaults to 10,000
  "provider": "grok-4-fast-reasoning"  // Optional
}

// Success Response
{
  "success": true,
  "response": "Deployment plan: ...",
  "mode": "swarm",
  "task_id": "pantheon_1_1738755600",
  "budget": {
    "used": 2847,
    "max": 15000,
    "remaining": 12153,
    "percentage": 18.98,
    "status": "OK"
  },
  "execution_time": 12.45,
  "permissions_checked": ["DATABASE"],
  "timestamp": "2026-02-05T12:00:00"
}

// Error Response (Budget Exhausted)
{
  "success": false,
  "error": "Token budget exhausted: 15,200 / 15,000",
  "error_type": "budget_exhausted",
  "budget_status": {...}
}

// Error Response (Permission Denied)
{
  "success": false,
  "error": "Permission denied for PAYMENTS: score 0.22 < 0.5",
  "error_type": "permission_denied"
}
```

### Get Budget Status

```javascript
GET /api/swarm/budget/pantheon_1_1738755600

// Response
{
  "initialized": true,
  "task_id": "pantheon_1_1738755600",
  "max_tokens": 15000,
  "used_tokens": 2847,
  "remaining_tokens": 12153,
  "usage_percentage": 18.98,
  "status": "OK",
  "can_continue": true
}
```

### Get Blackboard State

```javascript
GET /api/swarm/blackboard

// Response
{
  "success": true,
  "state": {
    "task:pantheon_1_1738755600:status": "completed",
    "task:pantheon_1_1738755600:description": "Deploy feature",
    "task:pantheon_1_1738755600:result": "..."
  },
  "key_count": 3
}

GET /api/swarm/blackboard/task:pantheon_1_1738755600:status

// Response
{
  "success": true,
  "key": "task:pantheon_1_1738755600:status",
  "value": "completed"
}
```

---

## 🔧 Auto-Permission Detection

Messages are automatically scanned for permission keywords:

```python
# DATABASE permission triggered by:
["deploy", "update", "delete", "schema", "migration"]

# PAYMENTS permission triggered by:
["payment", "charge", "refund", "transaction"]

# EMAIL permission triggered by:
["email", "send", "notify", "alert"]
```

**Example:**
- "Deploy new feature" → `["DATABASE"]`
- "Send payment confirmation email" → `["PAYMENTS", "EMAIL"]`
- "Explain AI agents" → `[]` (no permissions needed)

---

## 🎨 Frontend Integration Example

```javascript
// components/ChatSwarm.jsx

const sendSwarmMessage = async (message, budget = 10000) => {
  const response = await fetch('/api/chat-swarm', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      budget: budget
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    // Show response + budget status
    setResponse(data.response);
    setBudgetStatus({
      used: data.budget.used,
      max: data.budget.max,
      percentage: data.budget.percentage,
      status: data.budget.status
    });
    setTaskId(data.task_id);
  } else {
    // Handle errors
    if (data.error_type === 'budget_exhausted') {
      alert('Budget exceeded! Try a simpler query or increase budget.');
    } else if (data.error_type === 'permission_denied') {
      alert('Permission denied: ' + data.error);
    }
  }
};

// Budget display component
const BudgetMeter = ({ used, max, status }) => {
  const percentage = (used / max) * 100;
  const color = 
    status === 'EXHAUSTED' ? 'red' :
    status === 'CRITICAL' ? 'orange' :
    status === 'WARNING' ? 'yellow' : 'green';
  
  return (
    <div className="budget-meter">
      <div 
        className="budget-bar" 
        style={{
          width: `${percentage}%`,
          backgroundColor: color
        }}
      />
      <span>{used.toLocaleString()} / {max.toLocaleString()} tokens</span>
      <span className={`status-${status.toLowerCase()}`}>{status}</span>
    </div>
  );
};
```

---

## 🚀 Testing

### Start Dashboard

```bash
cd C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net
python web_dashboard.py
```

**Expected output:**
```
✓ Pantheon Swarm initialized with budget tracking & permission gates
Dashboard initialized with AI framework, Pantheon Swarm, MCP system, and multi-modal support
```

### Test with curl

```bash
# Test swarm chat
curl -X POST http://localhost:8000/api/chat-swarm \
  -H "Content-Type: application/json" \
  -d '{"message": "What are AI agents?", "budget": 5000}'

# Get budget status
curl http://localhost:8000/api/swarm/budget/pantheon_1_1738755600

# Get blackboard state
curl http://localhost:8000/api/swarm/blackboard
```

---

## 📊 Monitoring

### Budget Status Thresholds

- **OK** - 0-79% usage (green)
- **WARNING** - 80-89% usage (yellow)
- **CRITICAL** - 90-99% usage (orange)
- **EXHAUSTED** - 100%+ usage (red)

### Permission Evaluation

- **Score ≥ 0.5** → GRANTED
- **Score < 0.5** → DENIED

**Score formula:**
```
score = (trust_level × 0.4) + (justification_score × 0.4) + ((1 - risk) × 0.2)
```

---

## 🐛 Troubleshooting

### Issue: "Pantheon Swarm not initialized"

**Cause:** `pantheon_config.json` not found or PantheonSwarm import failed

**Solution:**
```bash
# Check config exists
ls pantheon_config.json

# Check import
python -c "from pantheon_swarm import PantheonSwarm; print('OK')"
```

### Issue: Permission always denied

**Solution:** Add detailed justification or use less risky operations

```javascript
// ❌ Weak justification
message: "Process payment"

// ✅ Strong justification
message: "User requested payment processing for order #12345 to complete checkout"
```

### Issue: Budget exhausts immediately

**Solution:** Increase budget for complex tasks

```javascript
// Small tasks
budget: 5000

// Medium tasks
budget: 10000

// Large tasks
budget: 20000
```

---

## 📈 Expected Benefits

**Cost Savings:**
- 30-50% token reduction via budget tracking
- Prevent $500 overnight bills
- Transparent usage for users

**Security:**
- Permission gates for DB/payments/email
- Complete audit trail
- Trust-based evaluation

**User Experience:**
- Real-time budget display
- Clear error messages
- Progress tracking via blackboard

---

## 📝 Next Steps

1. ✅ **Integration complete** - web_dashboard.py updated
2. ⏳ **Test locally** - Start dashboard and test endpoints
3. ⏳ **Add frontend UI** - Budget meter + swarm toggle
4. ⏳ **Deploy to production** - Push to Render
5. ⏳ **Monitor usage** - Track budget_tracking.json

---

## 🎯 Files Modified

- ✅ `web_dashboard.py` (+160 lines)
  - Import PantheonSwarm
  - Initialize in DashboardServer
  - Add /api/chat-swarm endpoint
  - Add 3 budget/blackboard endpoints
  - Auto-permission detection

---

**Author:** Neo 🔮  
**Status:** ✅ Ready to Test  
**Integration:** Complete
