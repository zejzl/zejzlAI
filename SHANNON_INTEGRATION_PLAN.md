# Shannon Integration Plan for zejzl.net

**Document Version:** 1.0  
**Created:** February 5, 2026  
**Author:** Neo  
**Status:** Technical Design - Ready for Review

---

## Executive Summary

This document outlines a phased integration plan for incorporating **Shannon** (production-grade multi-agent orchestration framework) into **zejzl.net** (9-Agent AI Pantheon system).

**Key Goals:**
1. Add production-grade monitoring, debugging, and cost control
2. Maintain existing Pantheon functionality
3. Enable gradual migration without breaking changes
4. Provide path to enterprise-ready infrastructure

**Recommended Approach:** Hybrid integration (Phase 1-3), with optional full migration (Phase 4)

**Timeline:** 3-4 weeks for full hybrid integration, 6-8 weeks if pursuing full migration

---

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Shannon Capabilities Assessment](#shannon-capabilities-assessment)
3. [Integration Architecture Options](#integration-architecture-options)
4. [Recommended Approach: Hybrid Integration](#recommended-approach-hybrid-integration)
5. [Technical Implementation Details](#technical-implementation-details)
6. [Migration Strategy](#migration-strategy)
7. [Testing and Validation](#testing-and-validation)
8. [Risks and Mitigations](#risks-and-mitigations)
9. [Timeline and Effort Estimates](#timeline-and-effort-estimates)
10. [Success Metrics](#success-metrics)

---

## Current Architecture Analysis

### zejzl.net Components (As Built)

**Core Infrastructure:**
```
└── zejzl_net/
    ├── ai_framework.py          # Multi-provider AI integration (Grok, Claude, etc.)
    ├── pantheon_rlm.py          # Pantheon Reinforcement Learning Manager
    ├── pantheon_swarm.py        # SwarmCoordinator wrapper (budget + permissions)
    ├── web_dashboard.py         # FastAPI server + dashboard
    ├── static/
    │   └── blackboard_dashboard.html  # Real-time monitoring UI
    └── skills/
        └── swarm-orchestrator/
            ├── swarm_guard.py       # Permission system
            ├── blackboard.py        # Shared state
            ├── budget_alerts.py     # Budget monitoring
            └── data/
                ├── budget_tracking.json
                ├── blackboard.md
                ├── active_grants.json
                └── audit_log.jsonl
```

**9-Agent Pantheon:**
- **Observer** (trust: 0.80) - Monitors input/context
- **Reasoner** (trust: 0.70) - Strategic analysis
- **Memory** (trust: 0.90) - Context management
- **Learner** (trust: 0.80) - Pattern recognition
- **Validator** (trust: 0.80) - Quality control
- **Analyzer** (trust: 0.80) - Deep analysis
- **Improver** (trust: 0.70) - Optimization
- **Actor** (trust: 0.50) - Action execution
- **Pantheon** (trust: 0.95) - Coordination (elevated privileges)

**Current Capabilities:**
✅ Budget tracking (token limits per task)
✅ Permission gates (DATABASE, PAYMENTS, EMAIL, FILE_EXPORT)
✅ Trust-based authorization (0.5 weighted score threshold)
✅ WebSocket real-time updates
✅ Blackboard shared state
✅ Audit logging (permission decisions)
✅ Discord alerts (80%/90%/100% budget thresholds)

**Current Limitations:**
❌ No step-by-step execution replay
❌ Limited debugging (can't rewind agent decisions)
❌ Basic monitoring (no Prometheus/OpenTelemetry)
❌ No code execution sandbox
❌ Manual model fallback (not automatic)
❌ Single-tenant only (no isolation between users)

---

## Shannon Capabilities Assessment

### Shannon Features Relevant to zejzl.net

**Source:** https://github.com/Kocoro-lab/Shannon

**Core Features:**
1. **Temporal Workflows** - Time-travel debugging, replay any execution
2. **Hard Token Budgets** - Automatic enforcement + model fallback
3. **Real-time Monitoring** - Dashboard, Prometheus metrics, OpenTelemetry
4. **Security Sandbox** - WASI for safe code execution
5. **Multi-Provider** - OpenAI, Anthropic, Google, DeepSeek, local models
6. **REST API + SSE** - HTTP API with Server-Sent Events streaming
7. **Multi-tenant Isolation** - OPA policies, separate workspaces

**Tech Stack:**
- **Go** - Core orchestration engine
- **Rust** - Performance-critical components
- **Docker** - Containerized deployment
- **Temporal** - Workflow engine (durable execution)
- **Prometheus** - Metrics collection
- **OpenTelemetry** - Distributed tracing

**Deployment:**
- Docker Compose for local development
- Native desktop app for monitoring
- Production-ready (battle-tested at scale)

**API Interface:**
```bash
# Submit task
POST http://localhost:8080/api/v1/tasks
{
  "query": "Your task here",
  "session_id": "user-session"
}

# Stream events
GET http://localhost:8080/api/v1/stream/sse?workflow_id=task-123

# Get result
GET http://localhost:8080/api/v1/tasks/task-123
```

**What Shannon Solves for Us:**
✅ **Debugging Pantheon decisions** - Replay Observer → Reasoner → Actor workflow step-by-step
✅ **Cost spirals** - Hard limits prevent runaway token usage (learned from $REGRET 😂)
✅ **Production monitoring** - Enterprise-grade observability
✅ **Security** - Sandbox for Actor agent code execution
✅ **Automatic fallback** - If Claude hits rate limit, auto-switch to Grok

---

## Integration Architecture Options

### Option A: Shannon-First (Full Replacement)

**Architecture:**
```
zejzl.net Frontend (React)
        ↓
Shannon REST API (localhost:8080)
        ↓
9-Agent Pantheon (as Shannon workflows)
        ↓
LLM Providers (OpenAI, Anthropic, xAI)
```

**Implementation:**
- Rewrite each Pantheon agent as a Shannon workflow
- Use Shannon's native budget/permission system
- Replace web_dashboard.py with Shannon's UI
- Discard PantheonRLM, pantheon_swarm.py, swarm_guard.py

**Pros:**
✅ Production-ready infrastructure from day 1
✅ Less code to maintain (Shannon handles orchestration)
✅ Best-in-class monitoring, debugging, security
✅ Multi-tenant ready (can support multiple users)

**Cons:**
❌ Throws away 6 weeks of existing work
❌ Steep learning curve (Go + Temporal)
❌ Tighter coupling to Shannon (vendor lock-in risk)
❌ 6-8 weeks for complete rewrite

**Verdict:** Too risky for initial integration. Save for v2.0 if hybrid approach proves Shannon's value.

---

### Option B: Hybrid Integration (Recommended)

**Architecture:**
```
zejzl.net Frontend (React)
        ↓
FastAPI Server (web_dashboard.py)
        ↓  ↓
        ↓  └──→ Shannon REST API (complex tasks)
        ↓              ↓
        ↓         Shannon Workflows (advanced features)
        ↓
PantheonRLM (simple tasks)
        ↓
9-Agent Pantheon (existing code)
        ↓
LLM Providers
```

**Implementation:**
- Keep existing Pantheon infrastructure
- Add Shannon as optional "power tool" for complex tasks
- Route decisions based on task complexity/requirements
- Share monitoring data between both systems

**Routing Logic:**
```python
def process_task(task):
    if task.requires_debugging or task.budget_critical:
        return shannon_client.submit(task)  # Use Shannon
    else:
        return pantheon_rlm.process_task(task)  # Use existing
```

**Pros:**
✅ Zero breaking changes to existing functionality
✅ Gradual migration path (add Shannon features incrementally)
✅ Learn Shannon without big-bang rewrite
✅ Keep existing dashboards + monitoring
✅ Low risk (can disable Shannon if issues arise)

**Cons:**
⚠️ Two orchestration systems to maintain
⚠️ More complexity (routing logic, dual monitoring)
⚠️ Some duplication (both systems track budgets)

**Verdict:** Best approach for Phase 1. Proves Shannon's value before committing fully.

---

### Option C: Shannon as Backend Only

**Architecture:**
```
zejzl.net Frontend (React)
        ↓
FastAPI Server (web_dashboard.py) - kept as-is
        ↓
PantheonRLM - kept as-is
        ↓
Shannon (replaces low-level execution only)
        ↓
LLM Providers
```

**Implementation:**
- Shannon handles only LLM calls + token tracking
- PantheonRLM keeps agent coordination logic
- Minimal changes to existing code

**Pros:**
✅ Minimal disruption
✅ Get Shannon's budget enforcement immediately
✅ Easier to implement than Option B

**Cons:**
❌ Doesn't leverage Shannon's workflow/debugging features
❌ Still need to maintain custom orchestration
❌ Miss out on 80% of Shannon's value

**Verdict:** Too limited. Option B gives us more upside for similar effort.

---

## Recommended Approach: Hybrid Integration

### Phase 1: Shannon Standalone Setup (Week 1)

**Goal:** Get Shannon running alongside zejzl.net without integration

**Tasks:**
1. **Install Shannon locally**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/Kocoro-lab/Shannon/v0.1.0/scripts/install.sh | bash
   ```

2. **Configure API keys**
   - Add existing keys (OpenAI, Anthropic, xAI Grok)
   - Test with simple queries
   - Verify Shannon dashboard works

3. **Run parallel to zejzl.net**
   - Shannon: localhost:8080
   - zejzl.net: localhost:8000
   - No integration yet, just validation

4. **Test Shannon features**
   - Submit tasks via REST API
   - View execution replay
   - Trigger budget limits
   - Test automatic model fallback

**Deliverables:**
- Shannon running on localhost:8080
- Documentation: SHANNON_SETUP.md
- Test results: Which features work best for our use case

**Effort:** 2-3 days  
**Owner:** Neo

---

### Phase 2: Shannon Integration Layer (Week 2)

**Goal:** Build bridge between zejzl.net and Shannon

**Architecture:**
```python
# shannon_client.py - New file
class ShannonClient:
    def __init__(self):
        self.base_url = "http://localhost:8080/api/v1"
    
    def submit_task(self, query, session_id, budget=10000):
        """Submit task to Shannon, return task_id"""
        response = requests.post(f"{self.base_url}/tasks", json={
            "query": query,
            "session_id": session_id,
            "budget": budget
        })
        return response.json()["task_id"]
    
    def stream_events(self, task_id):
        """SSE stream of execution events"""
        url = f"{self.base_url}/stream/sse?workflow_id={task_id}"
        return requests.get(url, stream=True)
    
    def get_result(self, task_id):
        """Poll for final result"""
        response = requests.get(f"{self.base_url}/tasks/{task_id}")
        return response.json()
```

**Integration Points:**

1. **Add Shannon routing to web_dashboard.py:**
```python
from shannon_client import ShannonClient

shannon = ShannonClient()

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # Existing logic
    if request.use_shannon:
        # Route to Shannon
        task_id = shannon.submit_task(
            query=request.message,
            session_id=request.session_id,
            budget=request.budget or 10000
        )
        return {"task_id": task_id, "via": "shannon"}
    else:
        # Route to PantheonRLM (existing)
        result = pantheon_rlm.process_task(request.message)
        return {"result": result, "via": "pantheon"}
```

2. **Add Shannon toggle to frontend:**
```javascript
// Add checkbox in chat UI
<input type="checkbox" id="useShannon" />
<label>Use Shannon (advanced debugging)</label>
```

3. **Add Shannon monitoring to blackboard dashboard:**
```html
<!-- New panel in blackboard_dashboard.html -->
<div class="panel">
    <h3>Shannon Tasks</h3>
    <div id="shannon-tasks">
        <!-- Live list of Shannon workflow executions -->
    </div>
</div>
```

**Deliverables:**
- `shannon_client.py` - Python client wrapper
- Updated `web_dashboard.py` - Shannon routing
- Updated `blackboard_dashboard.html` - Shannon monitoring panel
- Documentation: SHANNON_API.md

**Effort:** 5-7 days  
**Owner:** Neo

---

### Phase 3: Advanced Features (Week 3)

**Goal:** Leverage Shannon's unique capabilities

**Features to Add:**

#### 3.1 Execution Replay UI
```html
<!-- New page: shannon_replay.html -->
<div class="replay-controls">
    <button id="replayTask">Replay Task</button>
    <input type="text" placeholder="Task ID" id="taskId" />
</div>

<div class="execution-timeline">
    <!-- Step-by-step visualization of agent decisions -->
    <div class="step">Observer → "User wants to deploy code"</div>
    <div class="step">Reasoner → "Check git status first"</div>
    <div class="step">Actor → "Run git status"</div>
</div>
```

**API Integration:**
```python
@app.get("/api/shannon/replay/{task_id}")
async def replay_task(task_id: str):
    """Get step-by-step execution history"""
    history = shannon.get_execution_history(task_id)
    return {
        "steps": history,
        "total_tokens": sum(s["tokens"] for s in history),
        "duration_ms": history[-1]["timestamp"] - history[0]["timestamp"]
    }
```

#### 3.2 Budget Enforcement Integration
```python
# Update pantheon_swarm.py to use Shannon budgets
class PantheonSwarm:
    def process_task(self, message, budget=10000):
        # If budget critical, use Shannon
        if budget < 5000 or self.budget_exhausted:
            return shannon.submit_task(message, budget=budget)
        
        # Otherwise use existing PantheonRLM
        return self.coordinator.coordinate_task(message)
```

#### 3.3 Automatic Model Fallback
```python
# Shannon handles this automatically, but we can configure priority:
shannon_config = {
    "primary_model": "anthropic/claude-sonnet-4-5",
    "fallback_models": [
        "xai/grok-4-fast-reasoning",  # Fast + cheap
        "openai/gpt-4o-mini"           # Cheapest
    ],
    "fallback_triggers": {
        "rate_limit": True,   # Switch on 429
        "budget_80": True,    # Switch at 80% budget
        "latency_p99": 2000   # Switch if >2s response
    }
}
```

**Deliverables:**
- `shannon_replay.html` - Execution replay UI
- Updated budget enforcement logic
- Shannon configuration file
- Documentation: SHANNON_FEATURES.md

**Effort:** 5-7 days  
**Owner:** Neo

---

### Phase 4: Production Readiness (Week 4)

**Goal:** Make Shannon integration production-ready

**Tasks:**

#### 4.1 Error Handling
```python
class ShannonClient:
    def submit_task(self, query, session_id, budget=10000, retry=3):
        for attempt in range(retry):
            try:
                response = requests.post(...)
                return response.json()["task_id"]
            except requests.exceptions.ConnectionError:
                if attempt == retry - 1:
                    # Fallback to PantheonRLM
                    logger.warning("Shannon unavailable, using PantheonRLM")
                    return self._fallback_to_pantheon(query)
                time.sleep(2 ** attempt)  # Exponential backoff
```

#### 4.2 Monitoring Integration
```python
# Export Shannon metrics to our existing dashboard
@app.get("/api/shannon/metrics")
async def shannon_metrics():
    """Proxy Shannon's Prometheus metrics"""
    shannon_metrics = requests.get("http://localhost:8080/metrics")
    
    return {
        "active_workflows": parse_prometheus(shannon_metrics, "shannon_active_workflows"),
        "total_tokens": parse_prometheus(shannon_metrics, "shannon_total_tokens"),
        "error_rate": parse_prometheus(shannon_metrics, "shannon_error_rate")
    }
```

#### 4.3 Multi-Tenant Support (Future)
```python
# Shannon supports OPA policies for multi-tenant isolation
# We can configure tenant-specific budgets/permissions

shannon_tenants = {
    "user-123": {
        "monthly_budget": 100000,  # 100K tokens/month
        "allowed_models": ["gpt-4o-mini", "grok-4-fast"],
        "rate_limit": 100,  # 100 requests/hour
    },
    "user-456": {
        "monthly_budget": 500000,  # Premium tier
        "allowed_models": ["all"],
        "rate_limit": 500
    }
}
```

**Deliverables:**
- Production error handling
- Metrics integration
- Multi-tenant configuration (documented, not implemented yet)
- Load testing results (100 concurrent requests)
- Documentation: SHANNON_PRODUCTION.md

**Effort:** 5-7 days  
**Owner:** Neo

---

## Technical Implementation Details

### Dependencies to Add

**Python packages:**
```bash
# requirements.txt additions
requests>=2.31.0      # HTTP client for Shannon API
sseclient-py>=1.8.0   # Server-Sent Events parsing
prometheus-client>=0.19.0  # Metrics export
```

**Docker services:**
```yaml
# docker-compose.yml additions
services:
  shannon:
    image: waylandzhang/shannon:latest
    ports:
      - "8080:8080"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - XAI_API_KEY=${XAI_API_KEY}
    volumes:
      - ./shannon-data:/data
```

### File Structure After Integration

```
zejzl_net/
├── shannon_client.py          # NEW: Shannon API wrapper
├── shannon_config.py          # NEW: Shannon configuration
├── ai_framework.py            # KEEP: Multi-provider support
├── pantheon_rlm.py            # KEEP: Simple task coordinator
├── pantheon_swarm.py          # UPDATE: Add Shannon routing
├── web_dashboard.py           # UPDATE: Add Shannon endpoints
├── static/
│   ├── blackboard_dashboard.html   # UPDATE: Add Shannon panel
│   └── shannon_replay.html         # NEW: Replay UI
├── templates/
│   └── dashboard.html         # KEEP: Main dashboard
└── docs/
    ├── SHANNON_SETUP.md       # NEW
    ├── SHANNON_API.md         # NEW
    ├── SHANNON_FEATURES.md    # NEW
    └── SHANNON_PRODUCTION.md  # NEW
```

### API Endpoints to Add

```python
# New endpoints in web_dashboard.py

@app.post("/api/shannon/submit")
async def shannon_submit(request: ShannonTaskRequest):
    """Submit task to Shannon"""
    task_id = shannon.submit_task(
        query=request.message,
        session_id=request.session_id,
        budget=request.budget
    )
    return {"task_id": task_id}

@app.get("/api/shannon/status/{task_id}")
async def shannon_status(task_id: str):
    """Get task status"""
    return shannon.get_status(task_id)

@app.get("/api/shannon/replay/{task_id}")
async def shannon_replay(task_id: str):
    """Get execution replay data"""
    return shannon.get_replay(task_id)

@app.get("/api/shannon/metrics")
async def shannon_metrics():
    """Get Shannon metrics"""
    return shannon.get_metrics()
```

### Configuration Management

```python
# shannon_config.py
from pydantic import BaseSettings

class ShannonConfig(BaseSettings):
    # Shannon server
    shannon_url: str = "http://localhost:8080"
    
    # Model priority
    primary_model: str = "anthropic/claude-sonnet-4-5"
    fallback_models: list[str] = [
        "xai/grok-4-fast-reasoning",
        "openai/gpt-4o-mini"
    ]
    
    # Budget defaults
    default_budget: int = 10000
    budget_warning_threshold: float = 0.8
    budget_critical_threshold: float = 0.9
    
    # Routing
    use_shannon_for_complex: bool = True
    complexity_threshold: int = 5  # Tasks requiring >5 agents
    
    # Performance
    shannon_timeout: int = 30  # seconds
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
```

---

## Migration Strategy

### Gradual Migration Plan

**Phase 1 (Week 1):** Shannon standalone, no integration
- **Risk:** None (independent deployment)
- **Rollback:** Just stop Shannon container

**Phase 2 (Week 2):** Shannon optional, existing system default
- **Risk:** Low (Shannon routing is opt-in)
- **Rollback:** Disable Shannon routing flag

**Phase 3 (Week 3):** Shannon for specific use cases
- **Risk:** Medium (auto-routing based on task type)
- **Rollback:** Change routing logic back to PantheonRLM

**Phase 4 (Week 4+):** Shannon as primary (optional)
- **Risk:** High (Shannon becomes critical path)
- **Rollback:** Requires code revert + redeploy

### Decision Points

**After Phase 2 - Continue or Stop?**

**Continue if:**
✅ Shannon provides measurable value (better debugging, cost savings)
✅ No major stability issues
✅ Team comfortable with Shannon architecture

**Stop if:**
❌ Shannon adds complexity without clear benefit
❌ Frequent failures or performance issues
❌ Learning curve too steep

**After Phase 3 - Expand or Maintain?**

**Expand to Phase 4 if:**
✅ Shannon proves superior for most tasks
✅ Monitoring/debugging features heavily used
✅ Ready to commit to Shannon long-term

**Maintain hybrid if:**
⚠️ Both systems have unique strengths
⚠️ Not ready to deprecate existing Pantheon code

### Data Migration

**No data migration needed for hybrid approach:**
- Shannon uses its own database (Temporal)
- Existing blackboard.md, budget_tracking.json remain
- Both systems can read from shared state if needed

**If moving to Shannon-first:**
1. Export blackboard entries → Shannon workflows
2. Migrate budget history → Shannon metrics
3. Convert audit log → Shannon event stream

---

## Testing and Validation

### Test Plan

#### Unit Tests
```python
# test_shannon_client.py
def test_submit_task():
    client = ShannonClient()
    task_id = client.submit_task("Test query", "session-1", budget=1000)
    assert task_id.startswith("task-")

def test_fallback_on_failure():
    client = ShannonClient()
    # Mock Shannon failure
    with mock.patch('requests.post', side_effect=ConnectionError):
        result = client.submit_task_with_fallback("Test")
        assert result["via"] == "pantheon"  # Fell back
```

#### Integration Tests
```python
# test_shannon_integration.py
def test_end_to_end_task():
    # Submit via web_dashboard
    response = client.post("/api/shannon/submit", json={
        "message": "What's 2+2?",
        "session_id": "test"
    })
    task_id = response.json()["task_id"]
    
    # Wait for completion
    time.sleep(5)
    
    # Get result
    result = client.get(f"/api/shannon/status/{task_id}")
    assert result.json()["status"] == "completed"
    assert "4" in result.json()["result"]
```

#### Load Tests
```bash
# Load test with Apache Bench
ab -n 1000 -c 50 http://localhost:8080/api/v1/tasks

# Expected results:
# - Throughput: >100 requests/sec
# - P99 latency: <2 seconds
# - Error rate: <1%
```

#### Budget Tests
```python
def test_budget_enforcement():
    # Submit task with 100 token budget
    task_id = shannon.submit_task("Long query", budget=100)
    
    # Wait for completion
    time.sleep(5)
    
    # Verify task stopped at budget
    result = shannon.get_result(task_id)
    assert result["tokens_used"] <= 100
    assert result["status"] == "budget_exceeded"
```

### Validation Criteria

**Phase 1 Complete:**
✅ Shannon running stably for 7 days
✅ Can submit tasks via REST API
✅ Dashboard shows execution history
✅ Budget limits enforced correctly

**Phase 2 Complete:**
✅ zejzl.net can route tasks to Shannon
✅ Results display correctly in UI
✅ No regression in existing functionality
✅ Shannon fallback works when offline

**Phase 3 Complete:**
✅ Replay UI shows step-by-step execution
✅ Automatic model fallback tested
✅ Budget alerts integrated with Discord
✅ Documentation complete

**Phase 4 Complete:**
✅ Production error handling validated
✅ Load testing passed (100+ concurrent)
✅ Monitoring integrated with Prometheus
✅ Multi-tenant config documented

---

## Risks and Mitigations

### Risk 1: Shannon Adds Complexity Without Value

**Risk Level:** Medium  
**Impact:** High (wasted effort)

**Mitigation:**
- Phase 1 is validation-only (2-3 days investment)
- Clear success criteria before proceeding to Phase 2
- Can abort integration with minimal sunk cost

**Contingency:**
- If Shannon doesn't prove valuable after Phase 1, stop
- Document learnings in SHANNON_EVALUATION.md
- Consider alternative solutions (Langfuse, LangSmith)

---

### Risk 2: Shannon Docker Dependencies

**Risk Level:** Low  
**Impact:** Medium (deployment complexity)

**Mitigation:**
- Docker already used for zejzl.net development
- Shannon has production-tested Docker images
- Well-documented deployment process

**Contingency:**
- If Docker issues arise, Shannon supports native binary deployment
- Can run Shannon on separate server/VPS

---

### Risk 3: Learning Curve (Go + Temporal)

**Risk Level:** Medium  
**Impact:** Low (only if pursuing full migration)

**Mitigation:**
- Hybrid approach doesn't require Go knowledge
- Use Shannon via REST API only (black box)
- Only need Go if customizing Shannon internals

**Contingency:**
- Stick with hybrid approach (no Go needed)
- Hire contractor if full migration desired

---

### Risk 4: Shannon Maintenance/Updates

**Risk Level:** Medium  
**Impact:** Medium (dependency management)

**Mitigation:**
- Shannon is actively maintained (recent commits)
- Docker images handle updates automatically
- Loose coupling via REST API (easy to swap)

**Contingency:**
- If Shannon abandoned, can fork repository
- Hybrid architecture allows removal with minimal refactor

---

### Risk 5: Performance Overhead

**Risk Level:** Low  
**Impact:** Low (extra HTTP hop)

**Mitigation:**
- Shannon is Go-based (very fast)
- REST API adds <50ms latency
- Benefits (debugging, monitoring) outweigh cost

**Contingency:**
- Profile with load testing in Phase 4
- If performance issue, optimize or disable Shannon routing

---

## Timeline and Effort Estimates

### Phase 1: Shannon Standalone Setup
**Duration:** 1 week  
**Effort:** 2-3 days (Neo)

**Week 1 Schedule:**
- Monday-Tuesday: Install Shannon, configure, test
- Wednesday: Write documentation (SHANNON_SETUP.md)
- Thursday-Friday: Validate features, test budget limits

---

### Phase 2: Shannon Integration Layer
**Duration:** 1 week  
**Effort:** 5-7 days (Neo)

**Week 2 Schedule:**
- Monday-Tuesday: Build shannon_client.py
- Wednesday-Thursday: Add routing to web_dashboard.py
- Friday: Update dashboard UI, test integration

---

### Phase 3: Advanced Features
**Duration:** 1 week  
**Effort:** 5-7 days (Neo)

**Week 3 Schedule:**
- Monday-Tuesday: Build replay UI
- Wednesday: Integrate budget enforcement
- Thursday: Configure automatic fallback
- Friday: Testing and documentation

---

### Phase 4: Production Readiness
**Duration:** 1 week  
**Effort:** 5-7 days (Neo)

**Week 4 Schedule:**
- Monday: Error handling
- Tuesday-Wednesday: Monitoring integration
- Thursday: Load testing
- Friday: Documentation finalization

---

### Total Timeline: 3-4 Weeks

**Minimum viable integration:** 2 weeks (Phase 1-2)  
**Production-ready integration:** 4 weeks (Phase 1-4)  
**Full migration (optional):** +2-4 weeks

---

## Success Metrics

### Phase 1 Metrics
- [ ] Shannon uptime: >99% for 7 days
- [ ] Task completion rate: >95%
- [ ] Budget enforcement: 100% accurate
- [ ] Learning assessment: Shannon valuable for zejzl.net? (yes/no)

### Phase 2 Metrics
- [ ] Integration stability: Zero breaking changes to existing functionality
- [ ] Shannon routing success rate: >98%
- [ ] Fallback working: Confirmed via testing
- [ ] Developer satisfaction: Would we continue? (yes/no)

### Phase 3 Metrics
- [ ] Replay UI: Successfully debug 5+ real tasks
- [ ] Model fallback: Triggered 10+ times, worked correctly
- [ ] Budget savings: Measured cost reduction from automatic fallback
- [ ] Discord alerts: Integrated with existing notification system

### Phase 4 Metrics
- [ ] Load testing: 100 concurrent requests, <2s P99 latency
- [ ] Error handling: Zero unhandled exceptions in 7 days
- [ ] Monitoring: Prometheus metrics exported successfully
- [ ] Documentation: Complete and reviewed

### Overall Success Criteria

**Integration is successful if:**
✅ Shannon provides measurable debugging value (replay used weekly)
✅ Budget enforcement prevents cost overruns (0 incidents)
✅ Monitoring improves visibility (Prometheus metrics useful)
✅ No significant performance degradation (<100ms overhead)
✅ Team comfortable maintaining hybrid architecture

**Integration should be removed if:**
❌ Shannon frequently fails or causes issues
❌ Complexity outweighs benefits
❌ Debugging features rarely used
❌ Performance impact unacceptable

---

## Next Steps

### Immediate Actions (Before Starting Phase 1)

1. **Review this document** (Zejzl + Neo)
   - Confirm approach makes sense
   - Identify any concerns or blockers
   - Decide: Proceed with Phase 1?

2. **Prepare environment**
   - Verify Docker installed and working
   - Check port 8080 available
   - Ensure API keys ready

3. **Schedule Phase 1** (if approved)
   - Block 2-3 days for Shannon setup
   - Plan testing scenarios
   - Define success criteria

### Questions to Resolve

- [ ] Should we start with Shannon immediately or after zejzl.net API fix?
- [ ] Which Shannon features are highest priority? (replay? budget? monitoring?)
- [ ] Do we want Shannon in production from day 1 or just development?
- [ ] Should we document Shannon integration for other projects (trading bot)?

---

## Appendix A: Shannon Resources

**Official Documentation:**
- GitHub: https://github.com/Kocoro-lab/Shannon
- Docs: https://docs.shannon.run
- Docker Hub: https://hub.docker.com/u/waylandzhang

**Platform Setup Guides:**
- Ubuntu: https://github.com/Kocoro-lab/Shannon/blob/main/docs/ubuntu-quickstart.md
- Windows: https://github.com/Kocoro-lab/Shannon/blob/main/docs/windows-setup-guide-en.md
- Rocky Linux: https://github.com/Kocoro-lab/Shannon/blob/main/docs/rocky-linux-quickstart.md

**Community:**
- Issues: https://github.com/Kocoro-lab/Shannon/issues
- Contributing: https://github.com/Kocoro-lab/Shannon/blob/main/CONTRIBUTING.md

---

## Appendix B: Alternative Solutions Considered

### LangSmith (LangChain)
**Pros:** Great debugging, trace visualization  
**Cons:** Tightly coupled to LangChain, paid service  
**Verdict:** Good for LangChain users, we're multi-framework

### Langfuse
**Pros:** Open source, good observability  
**Cons:** Less mature than Shannon, no Temporal workflows  
**Verdict:** Lighter-weight option if Shannon too heavy

### Custom Solution
**Pros:** Full control, tailored to our needs  
**Cons:** 2-3 months development time, maintenance burden  
**Verdict:** Not worth it when Shannon exists

**Shannon wins because:**
- Production-ready infrastructure (battle-tested)
- Temporal workflows (unique debugging capability)
- Multi-provider support (matches our architecture)
- Active development (recent commits, responsive maintainers)

---

## Document Control

**Version History:**
- v1.0 (2026-02-05): Initial draft - comprehensive integration plan

**Review Status:**
- [ ] Technical review (Neo) - Complete
- [ ] Business review (Zejzl) - Pending
- [ ] Architecture review - Pending

**Approval:**
- [ ] Zejzl approval to proceed with Phase 1
- [ ] Budget approval (Shannon is free/open-source, but Docker resources)
- [ ] Timeline approval (4 weeks for full integration)

---

**Ready to begin Phase 1?** 🚀

Let me know if you want to proceed, adjust priorities, or need any section expanded!
