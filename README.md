# longevity-assistant

Personal AI assistant for daily health guidance, longevity routines, recovery, movement, breathwork, rhythm, and long-term personal support.

This repository contains the early product and technical foundation for a chat-first assistant that combines:

- guided daily support
- scoped knowledge retrieval over trusted sources
- personal context and rules
- preparation for voice, biomarker, and genetics workflows

## Current state

The project already includes:

- Next.js frontend for the chat experience in `src/frontend`
- FastAPI backend for assistant orchestration in `src/backend`
- shared contracts in `src/shared`
- initial Notion sync/audit plumbing
- production eval workflow in GitHub Actions

This is still an active build, not a finished production release.

## Local development

### Requirements

- Node.js with npm
- Python 3.11+
- local virtual environment in `.venv`

### Environment

Copy `.env.example` to `.env` and fill in the values you want to use locally.

Important:

- `.env` is local-only and is ignored by git
- runtime files under `data/runtime/` are also ignored by git
- do not commit personal health data, tokens, or private workspace exports

### Run the app

Frontend:

```powershell
npm run dev:frontend
```

Backend:

```powershell
npm run dev:backend
```

### Verification

Frontend build:

```powershell
npm run build:frontend
```

Production eval suite:

```powershell
npm run eval:production
```

## Repository structure

- `src/frontend/` - chat-first web client
- `src/backend/` - API, orchestration, services, tests
- `src/shared/` - shared contracts and types
- `docs/` - product, architecture, and implementation documents
- `scripts/` - local automation and developer scripts
- `integrations/` - integration-oriented assets and specs

## Key documents

- [Plan](docs/planning/01-plan.md)
- [Use cases](docs/product/02-use-cases.md)
- [MVP spec](docs/product/03-mvp-spec.md)
- [PRD](docs/product/04-prd.md)
- [Stable foundation](docs/product/05-stable-foundation-v5.md)
- [Technical backlog](docs/technical/05-technical-backlog.md)
- [Architecture foundation](docs/technical/06-architecture-foundation.md)
- [Implementation roadmap](docs/technical/07-implementation-roadmap.md)

## Safety and privacy

This repository is intended for code, architecture, and product work.

- Keep personal data, health data, API tokens, and private source exports out of git.
- Use placeholder values in examples and screenshots.
- If you discover a security issue, follow the guidance in [SECURITY.md](SECURITY.md).

## License

No open-source license has been selected yet. Until a license is added, default copyright applies.
