# Docker Deployment Guide for ZEJZL.NET

This guide covers deploying ZEJZL.NET using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- Internet connection for API calls

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/zejzl/zejzlAI.git
cd zejzlAI/zejzl_net
```

### 2. Configure Environment

Create your `.env` file with API keys:

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 3. Start Services

```bash
# Start all services (ZEJZL.NET + Redis)
docker-compose up -d

# View logs
docker-compose logs -f zejzl_net

# Stop services
docker-compose down
```

### 4. Access the Application

- **Interactive Menu**: The container runs the interactive CLI by default
- **Logs**: `docker-compose logs -f`
- **Redis Commander** (optional): http://localhost:8081

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://redis:6379` |
| `SQLITE_PATH` | SQLite fallback database | `/app/data/ai_framework.db` |
| `DEFAULT_PROVIDER` | Default AI provider | `grok` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `*_API_KEY` | AI provider API keys | (required for functionality) |

### Volumes

- `./data` - SQLite database persistence
- `./logs` - Application logs
- `redis_data` - Redis data persistence

## Docker Commands

### Build and Run

```bash
# Build the image
docker-compose build

# Start services
docker-compose up -d

# Rebuild after changes
docker-compose up -d --build
```

### Debugging

```bash
# View container logs
docker-compose logs zejzl_net

# Follow logs in real-time
docker-compose logs -f zejzl_net

# Enter container shell
docker-compose exec zejzl_net bash

# Check container health
docker-compose ps
```

### Management

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View resource usage
docker-compose stats
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   ZEJZL.NET     │    │     Redis       │
│   Container     │◄──►│   Container     │
│                 │    │   (Persistence) │
│ • AI Framework  │    │                 │
│ • 9-Agent       │    │ • Message Bus   │
│   Pantheon      │    │ • Conversation  │
│ • Magic System  │    │   History       │
│ • Self-Healing  │    │ • Magic State   │
└─────────────────┘    └─────────────────┘
```

## Production Deployment

### 1. Environment Setup

```bash
# Create production environment file
cp .env.example .env.production
# Edit with production API keys
```

### 2. Production Compose File

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  zejzl_net:
    environment:
      - LOG_LEVEL=WARNING
      - REDIS_URL=redis://redis:6379
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
    restart: always
```

### 3. Deploy Production

```bash
# Deploy with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale Redis for high availability (optional)
docker-compose up -d --scale redis=3
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   docker-compose logs redis
   # Ensure Redis container is healthy
   docker-compose ps
   ```

2. **API Key Issues**
   ```bash
   # Check environment variables
   docker-compose exec zejzl_net env | grep API
   ```

3. **Out of Memory**
   ```bash
   # Increase Docker memory limit
   # Docker Desktop: Settings > Resources > Memory
   ```

4. **Port Conflicts**
   ```bash
   # Change ports in docker-compose.yml
   # ports: ["8080:8000"]  # host:container
   ```

### Health Checks

```bash
# Check all services health
docker-compose ps

# Individual service health
docker-compose exec zejzl_net ./docker-entrypoint.sh python -c "print('OK')"
```

## Security Considerations

- **API Keys**: Never commit `.env` files to version control
- **Network**: Use internal Docker networks for service communication
- **Volumes**: Regularly backup persistent volumes
- **Updates**: Keep base images updated for security patches

## Performance Tuning

### Redis Configuration

```yaml
redis:
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
  deploy:
    resources:
      limits:
        memory: 1G
      reservations:
        memory: 512M
```

### Application Tuning

```yaml
zejzl_net:
  environment:
    - GOMAXPROCS=4  # For Go-based services if added
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G
```

## Development

### Local Development with Docker

```bash
# Mount source code for live reload
docker run -v $(pwd):/app -p 8000:8000 zejzl_net

# Development compose override
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Testing in Docker

```bash
# Run tests in container
docker-compose exec zejzl_net python -m pytest

# Run specific test
docker-compose exec zejzl_net python -m pytest test_basic.py::test_observer_agent
```

## Support

For issues and questions:
- Check logs: `docker-compose logs`
- Health checks: `docker-compose ps`
- Container inspection: `docker inspect <container_id>`

---

**Status**: Docker containerization complete ✅
**Ready for deployment**: Yes 🚀