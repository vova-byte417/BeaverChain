# BeaverChain CI/CD Configuration

This document describes the CI/CD pipeline setup for BeaverChain using GitHub Actions.

## 📋 Pipeline Overview

```
Code Push / PR → Lint → Test → Build → Security Scan → Docker Build → Release
```

## 🚀 Workflow Files

### 1. `ci.yml` - Main CI/CD Pipeline

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Tag pushes (`v*` tags)

**Jobs:**

| Job | Description |
|-----|-------------|
| `python-lint-test` | Runs flake8, black, isort linting and pytest with coverage for Python services |
| `frontend-lint-test-build` | Runs ESLint, TypeScript check, tests and builds React frontend |
| `go-lint-test` | Runs golangci-lint and tests for Go services |
| `security-scan` | Trivy filesystem scan, Gosec (Go), Bandit (Python) |
| `docker-build-push` | Builds multi-stage Docker image and pushes to GHCR (tag only) |
| `release` | Generates changelog and creates GitHub Release (tag only) |

### 2. `release.yml` - Automated Releases

**Triggers:**
- Push to `main` branch

**Features:**
- Uses Release Please to automatically generate release PRs
- Follows Semantic Versioning based on conventional commits
- Auto-generates changelog
- Auto-merges release PRs when CI passes

### 3. `pr-title.yml` - PR Title Enforcement

**Triggers:**
- Pull request opened/edited/synchronized

**Features:**
- Enforces conventional commit format for PR titles
- Ensures consistent commit history when squashing

## 📦 Docker Configuration

### Multi-Stage Dockerfile

The `Dockerfile` uses multi-stage builds for optimal image size:

1. **frontend-builder**: Builds React/Vite frontend (Node.js)
2. **go-builder**: Compiles Go services (static binaries)
3. **python-builder**: Installs Python dependencies
4. **production**: Final slim image with all services

**Image Size:** ~500MB (vs ~2GB for single-stage)

### Docker Compose

`docker-compose.yml` provides full local development environment including:

- PostgreSQL 16 (database)
- Redis 7.2 (cache/message queue)
- Milvus 2.3.5 (vector database)
- MinIO (object storage)
- Temporal (workflow engine)
- All application services
- Nginx (reverse proxy)

**Quick Start:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Scripts

### `scripts/auto-commit.sh`

Helper script for conventional commits with automatic versioning:

```bash
# Basic usage
./scripts/auto-commit.sh <type> <scope> <message>

# Examples
./scripts/auto-commit.sh feat frontend "Add model version comparison"
./scripts/auto-commit.sh -m fix model-registry "Fix database connection leak"
./scripts/auto-commit.sh -t feat model-registry "v1.0.0 MVP release"
```

**Options:**
- `-m, --milestone`: Mark as milestone (triggers minor version bump)
- `-p, --patch`: Trigger patch version bump
- `-M, --major`: Trigger major version bump
- `-t, --tag`: Create git tag after commit

## 📝 Commit Convention

We follow **Conventional Commits** specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description | Version Bump |
|------|-------------|--------------|
| `feat` | New feature | Minor |
| `fix` | Bug fix | Patch |
| `docs` | Documentation changes | - |
| `style` | Code style changes | - |
| `refactor` | Code refactoring | - |
| `test` | Adding/updating tests | - |
| `chore` | Maintenance tasks | - |
| `perf` | Performance improvements | Patch |
| `ci` | CI/CD changes | - |

### Scopes

- `model-registry` - Model versioning service
- `frontend` - React web UI
- `prompt-engine` - Prompt management service
- `guardrails` - Safety guardrails service
- `workflow` - Workflow orchestration
- `infra` - Infrastructure changes
- `deps` - Dependency updates

## 🔒 Security Features

1. **Trivy**: Container image and filesystem vulnerability scanning
2. **Gosec**: Go code security scanning
3. **Bandit**: Python code security scanning
4. **Codecov**: Code coverage tracking and enforcement
5. **Dependabot**: Automated dependency updates (to be configured)

## 🚢 Release Process

### Automatic Releases

1. Developer merges PR to `main`
2. Release Please analyzes commits and creates release PR
3. CI runs on release PR
4. Release PR is auto-merged
5. GitHub Release is created with changelog
6. Docker image is built and pushed to GHCR
7. Version tag is created

### Manual Releases

```bash
# Use auto-commit script with tag
./scripts/auto-commit.sh -t -M feat infra "v1.0.0 Major Release"

# Push tag
git push && git push --tags
```

## 📊 Monitoring

- **Code Coverage**: Codecov integration with PR comments
- **CI Status**: GitHub Actions dashboard
- **Release Notes**: Auto-generated on GitHub Releases
- **Changelog**: Auto-maintained CHANGELOG.md

## 🔑 Required Secrets

The following GitHub Secrets must be configured:

| Secret | Description |
|--------|-------------|
| `GITHUB_TOKEN` | Auto-provided by GitHub |
| `CODECOV_TOKEN` | Codecov integration token (optional) |

## 📚 Best Practices

1. **Always run tests locally** before pushing
2. **Use the auto-commit script** for consistent commit messages
3. **Keep PRs small** - smaller PRs = faster CI = fewer conflicts
4. **Never push directly to main** - always use PRs
5. **Review CI failures** promptly - don't let them pile up

## 🐛 Troubleshooting

### CI Failing on Lint
```bash
# For Python
black .
isort .
flake8 .

# For Frontend
npm run lint -- --fix
```

### Docker Build Failing
```bash
# Build locally first
docker build -t beaverchain .

# Check Dockerfile syntax
docker run --rm -i hadolint/hadolint < Dockerfile
```

### Tests Failing Locally
```bash
# Python
cd model_registry
pytest -v

# Frontend
cd frontend
npm run test

# Go
cd prompt_engine
go test -v ./...
```
