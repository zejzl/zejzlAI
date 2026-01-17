# Redis Setup Guide for ZEJZL.NET

Redis is optional but recommended for optimal Inter-Agent Message Bus performance. The system works fine with SQLite-only fallback.

## Why Redis?

- **Inter-Agent Pub/Sub**: Enables real-time message distribution between agents
- **Better Performance**: Faster than SQLite for message queuing
- **Distributed**: Can run agents across multiple machines
- **Automatic Expiration**: Built-in TTL for conversation cleanup

**Note**: AI Provider Bus uses SQLite regardless - Redis is only for Inter-Agent communication.

---

## Option 1: Docker (Recommended)

### Windows (Docker Desktop)

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. **Start Redis Container**
   ```bash
   docker run -d \
     --name zejzl-redis \
     -p 6379:6379 \
     redis:latest
   ```

3. **Verify Redis is Running**
   ```bash
   docker ps
   # Should show zejzl-redis container running

   docker exec -it zejzl-redis redis-cli ping
   # Should return: PONG
   ```

4. **Stop/Start Redis**
   ```bash
   docker stop zejzl-redis
   docker start zejzl-redis
   docker restart zejzl-redis
   ```

5. **Remove Redis Container**
   ```bash
   docker stop zejzl-redis
   docker rm zejzl-redis
   ```

### Linux/Mac (Docker)

```bash
# Start Redis
docker run -d --name zejzl-redis -p 6379:6379 redis:latest

# Verify
docker ps
docker exec -it zejzl-redis redis-cli ping

# Management
docker stop zejzl-redis
docker start zejzl-redis
docker restart zejzl-redis
```

---

## Option 2: Native Installation

### Windows

1. **Download Redis for Windows**
   - Install from: https://github.com/microsoftarchive/redis/releases
   - Or use Chocolatey: `choco install redis-64`

2. **Start Redis Server**
   ```cmd
   redis-server.exe
   ```

3. **Verify**
   ```cmd
   redis-cli.exe ping
   ```

### Linux (Ubuntu/Debian)

```bash
# Install
sudo apt update
sudo apt install redis-server

# Start service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify
redis-cli ping

# Check status
sudo systemctl status redis-server
```

### macOS

```bash
# Install via Homebrew
brew install redis

# Start service
brew services start redis

# Or run manually
redis-server

# Verify
redis-cli ping
```

---

## Testing Redis Connection

### From Python

```python
import asyncio
from messagebus import AsyncMessageBus

async def test_redis():
    bus = AsyncMessageBus(redis_url="redis://localhost:6379")
    try:
        await bus.initialize()
        print("Redis connected!")
    except Exception as e:
        print(f"Redis not available: {e}")
    finally:
        await bus.cleanup()

asyncio.run(test_redis())
```

### From Command Line

```bash
# Test connection
redis-cli ping

# Monitor all commands
redis-cli monitor

# Get info
redis-cli info

# List keys
redis-cli keys "*"

# Check specific conversation
redis-cli lrange conversation:default 0 -1
```

---

## Configuration

### Environment Variables

Add to `.env`:
```bash
REDIS_URL=redis://localhost:6379
```

### Custom Redis Host/Port

If Redis is on a different machine:
```bash
REDIS_URL=redis://192.168.1.100:6379
```

With password:
```bash
REDIS_URL=redis://:password@localhost:6379
```

---

## Troubleshooting

### "Connection refused" Error

**Cause**: Redis is not running

**Fix**:
- Check if Docker container is running: `docker ps`
- Start Redis: `docker start zejzl-redis` or `redis-server`

### "Permission denied" Error (Linux)

**Fix**:
```bash
sudo chown redis:redis /var/lib/redis
sudo chmod 755 /var/lib/redis
```

### Port Already in Use

**Fix**:
```bash
# Find process using port 6379
netstat -ano | findstr :6379  # Windows
lsof -i :6379                 # Linux/Mac

# Kill the process or use different port
docker run -d --name zejzl-redis -p 6380:6379 redis:latest
```

Then update `.env`:
```bash
REDIS_URL=redis://localhost:6380
```

---

## Performance Tuning

### Increase Max Memory

```bash
docker run -d \
  --name zejzl-redis \
  -p 6379:6379 \
  redis:latest \
  redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Persist Data

```bash
docker run -d \
  --name zejzl-redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:latest \
  redis-server --save 60 1 --loglevel warning
```

---

## What If I Don't Want to Use Redis?

**No problem!** ZEJZL.NET works perfectly without Redis:

1. **SQLite Fallback**: Automatically used when Redis unavailable
2. **Full Functionality**: All features work (with SQLite persistence)
3. **Agent Communication**: Agents still work via direct method calls
4. **No Configuration Needed**: Just skip Redis setup entirely

**Trade-offs**:
- No real-time pub/sub between agents
- Slightly slower message persistence
- Cannot distribute agents across machines

**Current Setup**: If you see "Redis not available, using SQLite" in logs - that's expected and fine!

---

## Docker Compose (Advanced)

For production deployment with Redis:

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  redis:
    image: redis:latest
    container_name: zejzl-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --save 60 1 --loglevel warning
    restart: unless-stopped

volumes:
  redis-data:
```

Run:
```bash
docker-compose up -d
docker-compose down
```

---

## Next Steps

1. **Start Redis** (if desired): Follow Option 1 or 2 above
2. **Test Connection**: Use test script or run framework
3. **Check Logs**: Look for "Redis connected" or "Using SQLite" message
4. **Continue Development**: System works either way!

---

*Last Updated: 2026-01-17*
*ZEJZL.NET Framework v0.0.1*