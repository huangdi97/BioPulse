# Infrastructure & Config Audit Report

**Project**: One Cloud Four Ends (一云四端)  
**Date**: 2026-06-16  
**Scope**: Docker, CI/CD, dependencies, migrations, deployment scripts

---

## 1. Config Files Summary

| File | Status | Notes |
|------|--------|-------|
| `pyproject.toml` | ✅ Found | Tool config only (ruff, pytest, mypy, coverage) — no project metadata |
| `.env` | ❌ MISSING | Referenced by docker-compose but not present in repo |
| `.codex/config.toml` | ❌ MISSING | Not present |
| `.gitignore` | ❌ MISSING | **Critical** — not committed |
| `alembic.ini` | ✅ Found | Points to `cloud/migrations/` |

---

## 2. pyproject.toml Issues

- **No project metadata**: Missing `[project]` section (name, version, description, Python requires, authors). Not a distributable Python package.
- **Ruff vs Black line-length mismatch**: Ruff = 150, Black = 100. This will cause conflicts if both are used.
- **Excessive per-file ignore list**: 40+ lines of `[tool.ruff.lint.per-file-ignores]` — many whole-directory ignores (`"**" = ["E501"]`) for line-length violations, suggesting widespread code quality debt.
- **pytest coverage omits**: `"**/migrations/*"` excluded from coverage — but migrations directory is empty anyway.

---

## 3. Dockerfiles — 10 Found

All 10 Dockerfiles follow the same pattern:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ ./shared/
COPY <service>/ ./<service>/
EXPOSE <port>
CMD ["uvicorn", "<module>.app.main:app", "--host", "0.0.0.0", "--port", "<port>"]
```

### 🚨 CRITICAL ISSUES

1. **Inconsistent requirements source**: 7 Dockerfiles use root `requirements.txt` but 3 use per-service requirements:
   - `clinical-ops/Dockerfile` → `COPY clinical-ops/requirements.txt ./requirements.txt`
   - `patient-engage/Dockerfile` → `COPY patient-engage/requirements.txt ./requirements.txt`  
   - `market-access/Dockerfile` → `COPY market-access/requirements.txt ./requirements.txt`
   - **Result**: Different services will have different dependency sets installed.

2. **Hyphen vs underscore in Python imports**: Docker copies `~/sales-assistant/` but CMD references `sales_assistant.app.main:app`. Python can't import packages with hyphens — works only if directory has `__init__.py` and runtime resolves it. Same issue with `clinical-ops/`, `patient-engage/`, `market-access/`.

3. **Running as root**: No `USER` directive in any Dockerfile.

4. **No `.dockerignore`**: Risks copying venv/, __pycache__, .git, and data/ into images.

5. **No multi-stage builds**: All dependencies (including dev tools like pytest, ruff) are installed in production images.

---

## 4. Docker Compose

### `docker-compose.yml` (12 services + Redis)

- **Services**: cloud (8000), sales-coach (8001), opportunity (8002), assistant (8003), sales-assistant (8004), pharma-intel (8006), market-access (8007), clinical-ops (8010), patient-engage (8011), management (8012), agent-compliance-monitor (8015), agent-anomaly-analysis (8016), redis (6379)
- **Healthchecks**: ✅ All service containers have healthchecks
- **Networks**: ✅ Single shared network `yysd-net`
- **Pros**: Unified compose file, healthchecks on all services, Redis uses pinned tag `7-alpine`
- **Cons**: No `depends_on` between services, no restart policies (except Redis), all use SQLite files (not production-grade for multi-service), `.env` expected but missing

### `docker-compose.monitoring.yml` 🚨 ISSUES

- **Uses `:latest` tags** for prometheus and grafana — will cause unpredictable breaking changes
- **Missing**: healthchecks, restart policies, volume persistence for Prometheus/Grafana data
- **Prometheus only scrapes**: `localhost:8000` (cloud service only) — all other 11 services unmonitored

---

## 5. CI/CD Workflow (`.github/workflows/ci.yml`)

Single workflow with **2 jobs**:

### Job 1: `lint-and-test`
- Python 3.12 setup
- `pip install -r requirements.txt` (installs ALL dependencies — slow)
- `ruff check .` linting
- `pytest -q` test suite
- Node.js 20 setup
- Frontend: `npm ci` + `npx tsc --noEmit`

### Job 2: `deploy`
- Runs only on master branch push
- Uses `appleboy/ssh-action@v1` with SSH key
- **Issues**:
  - 🚨 No Docker image registry — builds directly on production server
  - 🚨 SSH private key as GitHub secret — no SSH certificate auth or OIDC
  - 🚨 `git pull` on prod server could cause deployment conflicts
  - 🚨 `docker-compose build` on prod server uses server resources, no cache sharing
  - 🚨 No staging environment
  - 🚨 No database migration step in deploy job
  - No deployment rollback strategy
  - No notification of deployment status

---

## 6. Deployment Strategy

**Unified**: One `docker-compose.yml` manages all services together. Both `scripts/deploy.sh` and CI/CD use `docker compose build && docker compose up -d`.

- ✅ `deploy.sh` has comprehensive health checking for all 7 services
- ✅ All-or-nothing deployment ensures consistency
- ❌ Cannot deploy individual services independently
- ❌ No blue-green deployment support
- ❌ SQLite files are mounted as volumes — concurrent writes from multiple containers to SQLite is unsafe

**Also found**: `cloud-api.service` (systemd unit) for non-Docker direct deployment.

---

## 7. Dependencies

### 14 requirement files found:

| File | Dependencies | Scope |
|------|-------------|-------|
| `requirements.txt` (root) | 59 pinned | All services (combined) |
| `requirements-lock.txt` | ~144 pinned | Full lock file (includes transitive deps) |
| `cloud/requirements.txt` | 15 loose | Cloud + langgraph + transformers |
| `assistant/requirements.txt` | 8 loose | Basic FastAPI stack |
| `sales-assistant/requirements.txt` | 8 loose | Basic FastAPI stack |
| `opportunity/requirements.txt` | 8 loose | Basic FastAPI stack |
| `sales-coach/requirements.txt` | 8 loose | Basic FastAPI stack |
| `management/requirements.txt` | 6 loose | Minimal FastAPI |
| `pharma_intel/requirements.txt` | 6 loose | Minimal FastAPI |
| `patient-engage/requirements.txt` | 6 loose | Minimal FastAPI |
| `market-access/requirements.txt` | 6 loose | Minimal FastAPI |
| `clinical-ops/requirements.txt` | 6 loose | Minimal FastAPI |
| `deploy/offline-assistant/requirements-offline.txt` | 4 loose | Offline deployment |

### Issues:
- 🚨 **No lock file used in Docker builds** — root `requirements.txt` uses pinned versions but per-service files use `>=` ranges, so builds are non-reproducible
- 🚨 **Root requirements.txt includes dev/test deps** (pytest, ruff, coverage, pre-commit) — these get installed in production Docker images
- **Duplicated dependencies** across 10 files makes maintenance harder
- **alembic is in requirements-lock.txt** but missing from any requirements.txt — it won't be installed in production unless manually added

---

## 8. Alembic / Database Migrations

### Status: ⚠️ SET UP BUT EMPTY

- `alembic.ini` → configured at `cloud/migrations/`
- `cloud/migrations/env.py` → pulls `database_url` from `shared.config.settings`
- `cloud/migrations/script.py.mako` → standard template present
- `cloud/migrations/versions/` → **EMPTY (0 migrations)**
- `target_metadata = None` → no autogenerate support (needs SQLAlchemy Base metadata)

**Issues**:
- 🚨 Migration infrastructure exists but has never been used
- 🚨 `target_metadata = None` means `alembic revision --autogenerate` won't detect schema changes
- 🚨 Only covers `cloud` service — the other 9+ services have no migration system at all
- SQLite databases in `data/` are manually created by application startup code, not by migrations

---

## 9. .gitignore — ❌ MISSING

No `.gitignore` file exists in the repository. This means:
- `venv/`, `__pycache__/`, `.pyc` files, `.db` files, `coverage_html/`, `node_modules/`, and IDE files are not excluded from tracking
- 🚨 **Production database files** (`data/*.db`) could be accidentally committed
- 🚨 **Secrets/credentials** in `.env` are at risk if `.env` is ever created in the tracked dir

---

## 10. Deploy Directory

| Path | Contents |
|------|----------|
| `deploy/prometheus/prometheus.yml` | Scrapes only `localhost:8000` (cloud) — all other services missing |
| `deploy/offline-assistant/README.md` | Offline deployment guide for assistant service |
| `deploy/offline-assistant/requirements-offline.txt` | Minimal deps for offline mode |

---

## 11. Scripts Directory — 13 Files

| Script | Purpose | Quality |
|--------|---------|---------|
| `deploy.sh` | Full deployment with health checks | ✅ Good |
| `backup_db.sh` | SQLite backup + 30-day retention | ✅ Good |
| `backup.sh` | SQLite backup using `.backup` | ✅ Good |
| `pg_dump.sh` | PostgreSQL backup (env-configurable) | ✅ Forward-looking |
| `run.sh` | Dev server with `--reload` | ✅ Simple |
| `install_deps.sh` | apt + pip install | ⚠️ Basic |
| `cron.example` | Cron documentation | ✅ Helpful |
| `cron_backup` | Actual cron entry | ✅ Ready |
| `logrotate.conf` | Log rotation config | ✅ Good |
| `cleanup_expired_recordings.py` | Audio file cleanup | ✅ Well-written |
| `download_layer1_model.py` | ML model download | ✅ Well-written |
| `backup_schedule.md` | Backup documentation | ✅ Good |

---

## 12. Security Issues Summary

| # | Issue | Severity |
|---|-------|----------|
| 1 | No `.gitignore` — risk of committing secrets/databases | 🔴 HIGH |
| 2 | No `.dockerignore` — large image sizes, risk of leaking data | 🔴 HIGH |
| 3 | Docker containers run as root | 🟡 MEDIUM |
| 4 | Monitoring compose uses `:latest` tags | 🟡 MEDIUM |
| 5 | CI/CD deploys via SSH private key on master branch | 🟡 MEDIUM |
| 6 | No Docker registry — builds happen on production server | 🟡 MEDIUM |
| 7 | `target_metadata = None` in alembic — migrations non-functional | 🟡 MEDIUM |
| 8 | No .env file in repository — no template for required variables | 🟡 MEDIUM |
| 9 | Dev dependencies installed in production Docker images | 🟡 MEDIUM |
| 10 | Hyphen/underscore mismatch in Docker copy vs Python imports | 🔴 HIGH |
| 11 | Inconsistent requirements.txt sources across Dockerfiles | 🟡 MEDIUM |
| 12 | Prometheus only monitors 1 of 12 services | 🟡 MEDIUM |
| 13 | SQLite used in multi-container setup — write conflicts possible | 🟡 MEDIUM |
