# 🐳 Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker 20.10+ and Docker Compose 2.0+
- `.env` file with all required credentials (see below)

### Start All Services
```bash
# Build and start both backend and dashboard
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Access Services
- **Backend API**: http://localhost:8080
- **Dashboard**: http://localhost:5173
- **API Health Check**: http://localhost:8080/
- **API Docs**: http://localhost:8080/docs (FastAPI auto-generated)

---

## Environment Configuration

### Required `.env` File

Create a `.env` file in the project root with the following variables:

```bash
# GitHub Configuration (REQUIRED)
GITHUB_TOKEN=ghp_your_github_personal_access_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
REPOSITORY_OWNER=your_username
REPOSITORY_NAME=your_repo_name

# LLM Provider (REQUIRED - choose one)
LLM_PROVIDER=gemini  # or openai, anthropic
GEMINI_API_KEY=your_gemini_key_here
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here

# Review Provider (OPTIONAL)
REVIEW_PROVIDER=llm  # or jules
# JULES_API_KEY=your_jules_key_here
# JULES_SOURCE_ID=sources/github/owner/repo

# Service Configuration (Docker defaults)
HOST=0.0.0.0  # Required for Docker networking
PORT=8080
DEBUG=False

# Automation Behavior
TRIGGER_MODE=both  # pr, push, or both
GROUP_AUTOMATION_UPDATES=True
POST_REVIEW_ON_PR=True
TRIVIAL_CHANGE_FILTER_ENABLED=True
```

### Minimal `.env` Example
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=my_secret_123
REPOSITORY_OWNER=myusername
REPOSITORY_NAME=myrepo
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
HOST=0.0.0.0
PORT=8080
```

---

## Architecture

### Services

#### Backend (`automation-agent-backend`)
- **Image**: Built from root `Dockerfile`
- **Port**: 8080 (mapped to host:8080)
- **Health Check**: `GET /` every 30s
- **Volumes**:
  - Source code (development mode)
  - Persistent data: `session_memory.json`, `coverage.xml`
  - Documentation: `spec.md`, `README.md`, `ARCHITECTURE.md`

#### Dashboard (`automation-agent-dashboard`)
- **Image**: Built from `dashboard/Dockerfile` (multi-stage with nginx)
- **Port**: 80 (mapped to host:5173)
- **Health Check**: HTTP probe every 30s
- **API Proxy**: Requests to `/api/*` proxied to backend:8080

### Networking
- Both services connected via `automation-network` bridge
- Dashboard communicates with backend using service name `backend`
- External access via mapped ports

---

## Production Deployment

### Remove Development Volumes
For production, edit `docker-compose.yml` to remove source code mounts:

```yaml
volumes:
  # Remove this line for production:
  # - ./src:/app/src
  
  # Keep only data volumes:
  - ./session_memory.json:/app/session_memory.json
  - ./coverage.xml:/app/coverage.xml
  - ./spec.md:/app/spec.md
  - ./README.md:/app/README.md
```

### Use Docker Secrets (Recommended)
Instead of `.env` file, use Docker secrets for sensitive data:

```yaml
services:
  backend:
    secrets:
      - github_token
      - gemini_api_key
    environment:
      - GITHUB_TOKEN_FILE=/run/secrets/github_token
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key

secrets:
  github_token:
    file: ./secrets/github_token.txt
  gemini_api_key:
    file: ./secrets/gemini_api_key.txt
```

### Resource Limits
Add resource constraints for production:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Missing .env file
# 2. Invalid API keys
# 3. Port 8080 already in use

# Verify environment variables
docker-compose exec backend env | grep GITHUB_TOKEN
```

### Dashboard Can't Connect to Backend
```bash
# Check network connectivity
docker-compose exec dashboard wget -O- http://backend:8080/

# Verify nginx proxy configuration
docker-compose exec dashboard cat /etc/nginx/conf.d/default.conf
```

### Health Checks Failing
```bash
# Check health status
docker-compose ps

# Manual health check
docker-compose exec backend curl -f http://localhost:8080/
docker-compose exec dashboard wget --spider http://localhost/
```

### Rebuild After Changes
```bash
# Rebuild specific service
docker-compose build backend
docker-compose build dashboard

# Rebuild and restart
docker-compose up --build -d
```

---

## Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f dashboard

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Container Stats
```bash
# Real-time resource usage
docker stats automation-agent-backend automation-agent-dashboard
```

### Health Status
```bash
# Check health of all services
docker-compose ps

# Detailed inspection
docker inspect automation-agent-backend | grep -A 10 Health
```

---

## Backup and Restore

### Backup Session Data
```bash
# Backup session memory
docker cp automation-agent-backend:/app/session_memory.json ./backup/

# Backup all data
docker-compose exec backend tar czf /tmp/backup.tar.gz \
  session_memory.json coverage.xml spec.md README.md
docker cp automation-agent-backend:/tmp/backup.tar.gz ./backup/
```

### Restore Data
```bash
# Restore session memory
docker cp ./backup/session_memory.json automation-agent-backend:/app/

# Restart to apply
docker-compose restart backend
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Create .env file
        run: |
          echo "GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}" >> .env
          echo "GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}" >> .env
          # ... add other vars
      
      - name: Build and deploy
        run: |
          docker-compose build
          docker-compose up -d
      
      - name: Health check
        run: |
          sleep 10
          curl -f http://localhost:8080/ || exit 1
```

---

## Security Best Practices

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Use Docker secrets** for production credentials
3. **Run as non-root user** - Add to Dockerfile:
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```
4. **Scan images** for vulnerabilities:
   ```bash
   docker scan automation-agent-backend
   ```
5. **Use specific image tags** instead of `latest`
6. **Enable Docker Content Trust**:
   ```bash
   export DOCKER_CONTENT_TRUST=1
   ```

---

## Next Steps

- [ ] Configure webhook URL in GitHub repository settings
- [ ] Set up reverse proxy (nginx/Caddy) for HTTPS
- [ ] Configure log aggregation (ELK stack, Loki)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Implement automated backups
- [ ] Configure auto-scaling (Docker Swarm/Kubernetes)
