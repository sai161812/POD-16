# POD-16

**A private, programmable backend for personal data, state, and decision logic.**

POD-16 is the backend I want my personal software to depend on.

Instead of letting every assistant, CLI, automation script, dashboard, or future agent maintain its own copy of projects, tasks, notes, goals, learning data, and preferences, POD-16 exposes one structured API as the source of truth.

It is intentionally built as a **single-user backend with multiple trusted clients**.

```text
PLUMA / CLI / Apps / Agents / Automations
                   │
                   ▼
               POD-16 API
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
      Data       Rules     Computed Views
        │          │          │
        └──────────┼──────────┘
                   ▼
               PostgreSQL
```

The interesting part is not the CRUD.

POD-16 also models relationships, derives state, evaluates user-defined rules, computes attention/focus views, maintains scoped client identities, and records mutation history without turning the application into a workflow engine.

---

## Why this exists

Personal software tends to accumulate state in the wrong places:

- an assistant has one task model,
- a dashboard has another,
- scripts keep their own JSON,
- project information gets duplicated,
- automation logic ends up hard-coded into clients,
- and eventually no system knows which copy is authoritative.

POD-16 moves that responsibility behind an API.

Clients do not know how the database is structured. They depend on stable HTTP contracts.

That gives me one place to define:

- what my data looks like,
- how entities relate,
- which state is stored,
- which state is derived,
- what each client is allowed to access,
- and what rules determine whether something needs attention.

The design principle is simple:

> **Store facts. Compute consequences.**

---

## Architecture

POD-16 is a **modular monolith** built with FastAPI, SQLAlchemy and PostgreSQL.

I deliberately did not split the system into microservices. The domains are independent enough to have clear boundaries, but they belong to the same consistency boundary and are deployed together.

```mermaid
flowchart TD
    C[Client] --> API[FastAPI /v1]

    API --> AUTH[Authentication + Scope Check]
    AUTH --> AUDIT[Request Audit Dependency]

    AUDIT --> ROUTER[Domain Router]
    ROUTER --> SERVICE[Service Layer]
    SERVICE --> REPO[Repository Layer]
    REPO --> DB[(PostgreSQL)]

    SERVICE --> RULES[Rules Engine]
    RULES --> FACTS[Fact Builders]

    FACTS --> DB
    RULES --> ATTENTION[Attention View]

    SERVICE --> FOCUS[Focus View]
    SERVICE --> SEARCH[Unified Search]
```

### Request flow

```text
HTTP request
    ↓
request ID
    ↓
API-key authentication
    ↓
scope authorization
    ↓
audit context
    ↓
router
    ↓
Pydantic validation
    ↓
service/domain logic
    ↓
repository
    ↓
SQLAlchemy
    ↓
PostgreSQL
```

Routers deal with HTTP.

Services own domain behaviour.

Repositories own persistence queries.

Models describe storage.

Schemas define API contracts.

Computed domains such as `focus` and `attention` deliberately have no database table.

---

## What POD-16 currently models

### Projects

Projects support:

- status and priority
- progress tracking
- target dates
- focus ranking
- parent projects
- flexible metadata
- completion semantics
- soft deletion and restoration

Completing a project automatically normalizes relevant state such as progress and completion time.

### Tasks

Tasks support:

- projects and parent tasks
- priority and lifecycle state
- date-based or timestamp-based deadlines
- scheduling
- estimates and ordering
- task dependencies
- dependency-cycle detection
- parent-cycle detection
- blocked-state derivation
- today / overdue / upcoming views
- soft deletion and restoration

Dependencies are enforced, not merely stored.

If:

```text
Task B → depends on → Task A
```

then B cannot move into `in_progress` or `completed` until A is complete.

POD-16 also prevents deleting an incomplete prerequisite while active tasks still depend on it.

### Notes

Notes are lightweight structured records that can optionally belong to projects.

They support:

- full CRUD
- project association
- metadata
- text search
- soft deletion
- restoration

### Goals

Goals support:

- lifecycle state
- progress
- target dates
- project associations
- completion semantics
- soft deletion and restoration

Goals and projects use an explicit many-to-many relationship instead of embedding IDs into JSON.

### Skills and learning

Skills track:

- current level
- target level
- category
- target date
- notes
- metadata

Learning sessions record actual work against a skill:

```text
skill
 ├── session
 ├── session
 └── session
```

POD-16 derives progress statistics such as:

- session count
- total learning time
- latest session
- remaining level gap

### Resources

Resources represent material I may want to consume or reference:

- books
- papers
- courses
- articles
- videos
- documentation
- repositories
- files
- tools
- websites

Resources support progress tracking and can be linked to skills.

### Personal profile

`/v1/profile` is intentionally a singleton resource.

It stores personal configuration such as:

- display name
- timezone
- locale
- preferences
- metadata

A singleton key is used instead of inventing an unnecessary UUID for a resource that can only have one instance.

---

## Derived state instead of duplicated state

POD-16 avoids storing values that can be reliably computed.

For example, a task's dependency state is not represented by a manually maintained:

```json
{
  "blocked": true
}
```

Instead:

```text
task dependencies
       ↓
current prerequisite states
       ↓
derived blocker state
```

The same idea is used for focus and attention.

This prevents stored state from drifting away from reality.

---

## Rules engine

POD-16 contains a small deterministic rules engine for expressing personal decision logic without embedding that logic into every client.

A rule consists of:

```text
domain
conditions
match mode
effects
```

Example:

```json
{
  "name": "Critical todo attention",
  "domain": "task",
  "match_mode": "all",
  "conditions": [
    {
      "field": "priority",
      "operator": "eq",
      "value": "critical"
    },
    {
      "field": "status",
      "operator": "eq",
      "value": "todo"
    }
  ],
  "effects": [
    {
      "type": "attention",
      "value": true
    },
    {
      "type": "label",
      "value": "critical-todo"
    },
    {
      "type": "score",
      "value": 40
    },
    {
      "type": "message",
      "value": "Critical task has not been started."
    }
  ]
}
```

Evaluation works like this:

```text
stored entity
    ↓
fact builder
    ↓
normalized facts
    ↓
enabled rules
    ↓
condition evaluation
    ↓
effects
```

Supported effects currently include:

- attention
- labels
- scores
- messages

Rules **do not mutate domain entities**.

That constraint is intentional. Evaluation remains deterministic and observable rather than introducing hidden side effects.

A rule can be evaluated directly:

```http
GET /v1/rules/evaluate/task/{task_id}
```

---

## Attention

`GET /v1/attention` evaluates current entities against enabled rules and returns only relevant matches.

For example:

```text
task:
    priority = critical
    status   = todo

rule:
    critical + todo
    → attention
    → score +40
```

The task appears in the attention view.

Change its priority:

```text
critical → normal
```

and it disappears automatically.

No `requires_attention` column needs to be synchronized.

Attention can currently be computed across:

- tasks
- projects
- goals
- resources
- skills

---

## Focus

`GET /v1/focus` provides a separate computed operational view of current work.

It combines information such as:

- explicitly focused projects
- relevant active tasks
- due and scheduled work
- linked goals
- dependency blockers

`focus` and `attention` solve different problems:

```text
focus      → what am I currently working around?
attention  → what do my rules say deserves attention?
```

Neither is stored as its own table.

---

## Search

POD-16 exposes unified search across:

- projects
- tasks
- notes
- goals
- resources
- skills

```http
GET /v1/search?q=transformer
```

Results are ranked using straightforward deterministic rules:

```text
exact title
    ↓
title prefix
    ↓
title contains query
    ↓
body contains query
```

Search input is escaped before being passed into SQL `ILIKE`, so characters such as `%` and `_` are treated as user input rather than accidental SQL wildcard operators.

This is intentionally simple today. PostgreSQL full-text search can replace it later if actual usage justifies the additional machinery.

---

## Authentication and client isolation

Every `/v1/*` request requires a Bearer API key.

POD-16 supports two types of credentials.

### Bootstrap key

The bootstrap key is the administrative escape hatch.

It has wildcard access and is intended for setup and emergency administration.

Production configuration refuses to start when the bootstrap key is still using the development placeholder or is shorter than the minimum accepted length.

### Client API keys

Individual applications can receive persistent API keys with explicit scopes.

Example:

```json
{
  "name": "pluma",
  "scopes": [
    "projects:read",
    "tasks:read",
    "tasks:write",
    "focus:read",
    "attention:read"
  ]
}
```

A generated client credential is returned **once** at creation.

POD-16 stores only its SHA-256 token hash, not the raw key.

Requests are authorized against domain scopes such as:

```text
tasks:read
tasks:write
projects:read
resources:write
rules:read
attention:read
clients:manage
```

Keys can be revoked without changing credentials used by other clients.

The API also tracks the last use time of persistent client credentials.

---

## Activity history

Successful mutations are automatically recorded as activity events.

An audit entry can identify:

- authenticated client
- domain
- HTTP method
- route operation
- concrete request path
- entity ID when available
- path parameters
- request ID
- timestamp

Request bodies are deliberately not written to the audit log.

That avoids turning an operational history feature into another store for note contents, credentials, or arbitrary sensitive payloads.

Activity history is not event sourcing. PostgreSQL domain tables remain the source of truth.

---

## API surface

The current API is organized under `/v1`.

| Domain | Base endpoint | Purpose |
|---|---|---|
| Profile | `/v1/profile` | Personal configuration |
| Projects | `/v1/projects` | Projects and hierarchy |
| Tasks | `/v1/tasks` | Work items, scheduling and dependencies |
| Notes | `/v1/notes` | Project-linked notes |
| Goals | `/v1/goals` | Goals and project relationships |
| Skills | `/v1/skills` | Skills, learning sessions and progress |
| Resources | `/v1/resources` | Learning/reference resources |
| Focus | `/v1/focus` | Computed current-focus view |
| Search | `/v1/search` | Cross-domain search |
| Rules | `/v1/rules` | Programmable decision rules |
| Attention | `/v1/attention` | Rule-derived attention view |
| Activity | `/v1/activity` | Mutation audit history |
| Clients | `/v1/clients` | Scoped API-client management |

FastAPI exposes the complete request/response schema through OpenAPI:

```text
/docs
```

---

## Pagination

Collection endpoints use bounded offset pagination:

```http
GET /v1/tasks?limit=50&offset=0
GET /v1/tasks?limit=50&offset=50
```

Queries use deterministic ordering with stable ID tie-breakers where needed so adjacent pages do not rely on ambiguous timestamp ordering.

Cursor pagination would add complexity without solving a real problem at POD-16's expected personal-data scale, so offset pagination is used deliberately.

---

## Error model

Application errors use a consistent envelope.

Example:

```json
{
  "error": {
    "code": "task_dependency_not_satisfied",
    "message": "This task cannot be started or completed until all dependencies are completed.",
    "details": {
      "blocked_by": []
    },
    "request_id": "..."
  }
}
```

Errors use stable machine-readable codes so clients do not need to parse human-readable messages.

Request IDs are also returned through:

```text
X-Request-ID
```

and may be supplied by the caller when tracing a request across systems.

---

## Data integrity

Important constraints exist at multiple layers.

```text
API schema validation
        ↓
domain/service validation
        ↓
database constraints
```

Examples include:

- task dependency cycle prevention
- task parent cycle prevention
- project self-parent prevention
- single task due mode (`due_date` or `due_at`)
- progress bounds
- positive learning duration
- skill level constraints
- slug uniqueness
- foreign-key integrity
- PATCH null validation for required fields

The service layer handles behaviour that cannot reasonably be expressed as a database constraint, while PostgreSQL still protects structural invariants.

---

## Soft deletion

Primary personal-data domains use soft deletion.

```text
DELETE
  ↓
deleted_at = timestamp
```

Normal reads exclude deleted entities.

Supported domains expose restore operations so deletion is reversible without weakening ordinary query semantics.

This is useful for a personal system where accidental deletion is more likely than a legitimate need to physically destroy relational history.

---

## Project structure

```text
POD-16/
├── alembic/
│   └── versions/             # schema history
│
├── app/
│   ├── api/
│   │   └── v1/              # API composition
│   │
│   ├── core/
│   │   ├── config.py        # environment configuration
│   │   ├── errors.py        # application error model
│   │   ├── middleware.py    # request IDs
│   │   ├── patch.py         # PATCH integrity helpers
│   │   ├── query.py         # query/search helpers
│   │   └── security.py      # API-key authentication
│   │
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   │
│   └── domains/
│       ├── activity/
│       ├── attention/
│       ├── clients/
│       ├── focus/
│       ├── goals/
│       ├── notes/
│       ├── profile/
│       ├── projects/
│       ├── resources/
│       ├── rules/
│       ├── search/
│       ├── skills/
│       └── tasks/
│
├── tests/
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

Most persistent domains follow:

```text
model
schemas
repository
service
router
```

That structure is intentionally boring. A developer should be able to predict where database access, HTTP handling, and business logic live without searching the entire codebase.

---

## Running locally

### Requirements

- Python 3.14
- `uv`
- Docker

Clone the repository and create the environment file:

```bash
cp .env.example .env
```

On PowerShell:

```powershell
Copy-Item .env.example .env
```

Change the development bootstrap key in `.env` if the API will be accessible beyond your own machine.

Start PostgreSQL:

```bash
docker compose up -d db
```

Install dependencies:

```bash
uv sync
```

Apply all existing migrations:

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run python -m uvicorn app.main:app --reload
```

Then open:

```text
Swagger / OpenAPI: http://127.0.0.1:8000/docs
Health check:      http://127.0.0.1:8000/health
```

Authenticate in Swagger using the API key itself. Swagger adds the `Bearer` prefix.

For direct requests:

```text
Authorization: Bearer <API_KEY>
```

---

## Configuration

POD-16 uses environment variables prefixed with `POD16_`.

```env
POD16_ENV=development
POD16_DATABASE_URL=postgresql+psycopg://pod16:pod16@localhost:5432/pod16
POD16_BOOTSTRAP_API_KEY=change-me-before-deployment
POD16_LOG_LEVEL=INFO
POD16_TIMEZONE=Asia/Kolkata
```

Supported environments:

```text
development
test
production
```

Production mode performs additional validation and refuses insecure bootstrap-key configuration.

The real `.env` file is ignored by Git and must never be committed.

---

## Database migrations

Database schema changes are managed through Alembic.

Apply migrations:

```bash
uv run alembic upgrade head
```

Create a migration only when the database schema actually changes:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
```

Normal service/router behaviour changes do not require migrations.

---

## Testing

The test suite uses `pytest` and FastAPI's test client.

Run everything:

```bash
uv run pytest -q
```

Tests cover behaviour including:

- authentication
- scoped client credentials
- project/task/goal workflows
- dependency enforcement
- dependency-cycle detection
- focus computation
- resources and skills
- learning progress
- search
- wildcard-safe search
- rules evaluation
- attention computation
- activity auditing
- soft deletion and restoration
- pagination
- PATCH null validation
- production configuration

Database tests run inside an outer transaction with savepoints, allowing service code to call `commit()` normally while the fixture can still roll the test back afterward.

That keeps tests close to real application behaviour without leaving test data behind.

Static compilation check:

```bash
uv run python -m compileall app
```

---

## Engineering decisions

A few choices in POD-16 are deliberate.

**Modular monolith over microservices.**  
There is one user, one data authority, and one transactional database. Splitting this into services would create deployment and consistency problems without providing useful isolation.

**PostgreSQL over document storage.**  
Projects, tasks, goals, dependencies and learning records have real relationships and constraints. JSONB is used where flexibility is useful, not as an excuse to avoid schemas.

**UUIDv7 identifiers.**  
Persistent entities use time-ordered UUIDs rather than database-local integer identities.

**Facts over duplicated derived state.**  
Blocked status, attention and focus are derived from authoritative data rather than independently maintained flags.

**Non-mutating rules.**  
Rules explain and classify current state. They do not silently rewrite that state.

**Per-client credentials.**  
PLUMA, a CLI, an agent, and a dashboard should not need to share one permanent master credential.

**Soft deletion for personal records.**  
Accidental deletion should usually be recoverable.

**Offset pagination for current scale.**  
POD-16 is a personal system, not a billion-row public feed. Complexity is added when the workload requires it.

---

## Boundaries

POD-16 is deliberately **not**:

- a generic SaaS backend
- a multi-user platform
- a file-storage service
- an AI model
- a workflow orchestration engine
- a replacement for PostgreSQL
- a collection of arbitrary JSON blobs

Large files belong elsewhere. POD-16 may store their metadata or references.

AI systems can consume POD-16, but intelligence is not embedded into the data layer.

These boundaries keep the API useful without turning it into an everything-system.

---

## Where this is going

The core backend is intentionally usable without any one client.

The next consumers are expected to include things such as:

```text
POD-16
 ├── PLUMA
 ├── command-line tools
 ├── personal dashboards
 ├── automation scripts
 └── future local agents
```

The API contract remains the boundary.

A client can disappear and be rewritten without taking the personal data model with it.

---

## Status

POD-16 is under active development.

The core data model, authentication system, client scopes, audit history, dependency logic, search, rules engine, focus computation, attention computation, pagination, migration infrastructure and automated tests are implemented.

The current work is focused on final hardening and deployment/documentation rather than expanding the domain surface.

---

## License

No public license has been selected yet.