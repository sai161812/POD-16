# POD-16

POD-16 is a private personal programmable backend: one authoritative API for projects,
tasks, notes, resources, learning data, rules, and future personal applications.

## Current build slice

Implemented:
- FastAPI application foundation
- PostgreSQL configuration
- SQLAlchemy 2.x ORM
- Alembic migration infrastructure
- request IDs
- consistent application error envelope
- bootstrap Bearer API-key protection for `/v1`
- complete first `projects` CRUD domain
- soft deletion
- Docker Compose PostgreSQL
- baseline tests

Not yet implemented because the relevant domain has not been built:
- tasks
- notes
- resources
- skills / learning
- rules engine
- focus computation
- persistent per-client API keys/scopes
- cursor pagination

## Run locally

1. Install Python 3.14 and `uv`.
2. Copy environment config:

   Windows PowerShell:
   ```powershell
   Copy-Item .env.example .env
   ```

3. Change `POD16_BOOTSTRAP_API_KEY` in `.env`.

4. Start PostgreSQL:
   ```bash
   docker compose up -d db
   ```

5. Install dependencies:
   ```bash
   uv sync
   ```

6. Generate the first migration from the actual models:
   ```bash
   uv run alembic revision --autogenerate -m "create projects"
   ```

7. Apply migrations:
   ```bash
   uv run alembic upgrade head
   ```

8. Run POD-16:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

9. Open:
   - API docs: http://127.0.0.1:8000/docs
   - Health: http://127.0.0.1:8000/health

For `/v1/*`, use:

```text
Authorization: Bearer <POD16_BOOTSTRAP_API_KEY>
```

## Example project

```json
{
  "name": "PLUMA",
  "slug": "pluma",
  "description": "Local Windows AI assistant",
  "status": "active",
  "priority": "critical",
  "focus_rank": 1,
  "progress_percent": 80,
  "metadata": {}
}
```

POST it to `/v1/projects`.

## Architectural rule

Clients depend on POD-16's API contracts, never on its database tables.
