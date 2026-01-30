# 📋 Grokputer → zejzl_net Extraction Checklist

**Phase 1: Core Infrastructure**

## Files to Extract (Priority Order)

### 🔥 Critical (Do First)

- [ ] `grokputer/src/core/message_bus.py` → `zejzl_net/src/core/message_bus.py`
  - 776 lines
  - Features: Priority queuing, correlation IDs, broadcast, history
  - Dependencies: src/exceptions.py, src/utils/toon_utils.py (optional)
  - Test file: `test_messagebus_live.py` (works perfectly)

- [ ] `grokputer/src/exceptions.py` → `zejzl_net/src/exceptions.py`
  - Custom exception hierarchy
  - Error handling with retries
  - Graceful degradation

- [ ] `grokputer/src/core/logging_config.py` → `zejzl_net/src/core/logging_config.py`
  - JSON structured logging
  - Performance logging
  - Separate debug/error files

### ⭐ High Priority

- [ ] `grokputer/src/memory/backends/redis_store.py` → `zejzl_net/src/memory/backends/redis_store.py`
  - Episode storage with TTL
  - Context retrieval
  - Memory consolidation
  - **NOTE:** Update port 6379 → 6380 (our isolated Redis)

- [ ] `grokputer/src/observability/performance_monitor.py` → `zejzl_net/src/observability/`
  - Real-time metrics
  - Latency tracking
  - Throughput monitoring

- [ ] `grokputer/src/observability/deadlock_detector.py` → `zejzl_net/src/observability/`
  - Async deadlock detection
  - Stack trace capture
  - Alerting

### 🎯 Medium Priority

- [ ] `grokputer/src/utils/toon_utils.py` → `zejzl_net/src/utils/toon_utils.py`
  - Token-efficient serialization
  - 30-50% reduction in message size
  - Optional but valuable

- [ ] `grokputer/src/collaboration/orchestrator.py` (review & extract relevant parts)
  - MAF orchestration
  - Only extract what fits zejzl_net's use case

- [ ] `grokputer/src/workflow/` (selective extraction)
  - State machine execution
  - Healing/recovery logic
  - Learning from failures

---

## Pre-Extraction Prep

### 1. Backup Current Code
```bash
cd C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net
git checkout -b pre-grokputer-integration
git add -A
git commit -m "Backup before grokputer integration"
```

### 2. Create Integration Branch
```bash
git checkout -b grokputer-integration
mkdir -p src/core src/memory/backends src/observability src/utils
```

### 3. Run Baseline Benchmarks
```bash
# Benchmark current MessageBus
python -c "
import asyncio
import time
from messagebus import AsyncMessageBus, Message

async def bench():
    bus = AsyncMessageBus()
    await bus.initialize()
    
    start = time.time()
    for i in range(10000):
        msg = Message.create('test', 'bench', 'test')
        await bus.publish('test', msg)
    elapsed = time.time() - start
    
    print(f'Current: {10000/elapsed:.2f} msg/sec')
    await bus.cleanup()

asyncio.run(bench())
"
```

---

## Extraction Process (Step-by-Step)

### Step 1: Extract MessageBus

```bash
# Copy file
cp C:\Users\Administrator\Desktop\grokputer\src\core\message_bus.py \
   C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net\src\core\message_bus.py

# Copy test file
cp C:\Users\Administrator\Desktop\grokputer\src\tools\test_messagebus_live.py \
   C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net\test_messagebus.py
```

**Adaptation needed:**
```python
# In message_bus.py, update imports:
# FROM: from ..exceptions import MessageBusError, handle_error
# TO:   from src.exceptions import MessageBusError, handle_error

# FROM: from ..utils.toon_utils import ...
# TO:   from src.utils.toon_utils import ... (or comment out if not using TOON)
```

### Step 2: Extract Exceptions

```bash
cp C:\Users\Administrator\Desktop\grokputer\src\exceptions.py \
   C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net\src\exceptions.py
```

**No changes needed** - standalone module

### Step 3: Extract Logging Config

```bash
cp C:\Users\Administrator\Desktop\grokputer\src\core\logging_config.py \
   C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net\src\core\logging_config.py
```

**Configuration:** Update log paths to match zejzl_net structure

### Step 4: Test Integration

```bash
# Run MessageBus tests
cd C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net
python test_messagebus.py

# Expected output:
# ✅ 15K+ msg/sec
# ✅ <0.1ms latency
# ✅ Priority ordering works
# ✅ Request-response pattern works
# ✅ Broadcast works
```

### Step 5: Update ai_framework.py

**Replace old MessageBus usage:**
```python
# OLD:
from messagebus import AsyncMessageBus, Message

# NEW:
from src.core.message_bus import MessageBus, Message, MessagePriority
```

**Update initialization:**
```python
# OLD:
self.bus = AsyncMessageBus("redis://localhost:6379")
await self.bus.initialize()

# NEW:
self.bus = MessageBus(default_timeout=30.0, history_size=100)
self.bus.register_agent("observer")
self.bus.register_agent("reasoner")
# ... register all 9 Pantheon agents
```

**Update message sending:**
```python
# OLD:
msg = Message.create(content="task", sender="agent", provider="grok")
await self.bus.publish("channel", msg)

# NEW:
msg = Message(
    from_agent="observer",
    to_agent="reasoner",
    message_type="observation",
    content={"data": "..."},
    priority=MessagePriority.HIGH
)
await self.bus.send(msg)
```

---

## Testing Checklist

### Unit Tests
- [ ] MessageBus priority ordering
- [ ] Request-response pattern
- [ ] Broadcast to multiple agents
- [ ] Timeout handling
- [ ] Error recovery

### Integration Tests
- [ ] All 9 Pantheon agents communicate
- [ ] Memory storage/retrieval works
- [ ] Performance monitoring active
- [ ] Logging captures all events

### Performance Tests
- [ ] Sustained 15K+ msg/sec
- [ ] Latency <0.1ms for 95th percentile
- [ ] No memory leaks over 1 hour
- [ ] CPU usage <20% idle, <60% under load

### Regression Tests
- [ ] Existing ai_framework tests pass
- [ ] Pantheon task completion works
- [ ] Redis persistence unchanged
- [ ] API compatibility maintained

---

## Rollback Plan

If integration fails:

```bash
# Restore pre-integration state
git checkout pre-grokputer-integration

# Or cherry-pick good changes
git checkout grokputer-integration -- src/core/message_bus.py
```

---

## Documentation Updates

After successful integration:

- [ ] Update README.md with new MessageBus docs
- [ ] Add performance benchmarks section
- [ ] Document new observability features
- [ ] Update architecture diagrams
- [ ] Add migration guide for existing code

---

## Success Metrics

**Before Integration (Baseline):**
- MessageBus: ~1-3K msg/sec (Redis pub/sub)
- Latency: ~5-10ms
- Monitoring: None
- Memory: Basic Redis
- Error handling: Try/except blocks

**After Integration (Target):**
- MessageBus: 15K+ msg/sec
- Latency: <0.1ms
- Monitoring: Full observability
- Memory: Hierarchical + Redis backend
- Error handling: Custom exception hierarchy with retries

**Improvement:** 5-15x performance boost + production observability

---

## Timeline

**Day 1-2: MessageBus**
- Extract files
- Adapt imports
- Run tests
- Benchmark

**Day 3-4: Memory & Observability**
- Extract memory backend
- Add performance monitor
- Add deadlock detector
- Integration tests

**Day 5-7: ai_framework.py Integration**
- Update all agent code
- Migrate to new MessageBus
- Run full Pantheon tests
- Performance validation

**Week 2: Polish & Deploy**
- Documentation
- Code review
- Staging deployment
- Production rollout

---

## Notes

- Keep grokputer's AsyncIO purity - no sync blocking
- Maintain zejzl_net's clean architecture - don't bloat
- Test incrementally - don't big-bang integrate
- Benchmark everything - measure improvements
- Document as you go - future-you will thank you

---

**Status:** Ready to begin  
**Confidence:** HIGH  
**Risk:** LOW (incremental, tested components)

**LET'S BUILD SOMETHING GREAT** 🚀
