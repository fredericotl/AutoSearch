# AutoSearch

A Python/FastAPI backend that tracks daily prices for registered products and emails users when a price drops below what the recent history suggests.

A price has little meaning without historical context. AutoSearch builds that history automatically.

*Personal project focused on backend architecture. Design decisions are documented in [`ARCHITECTURE.md`](./ARCHITECTURE.md).*

---

## How it works

A scheduled job runs once a day. For each registered product, it captures the current price, stores it, and evaluates whether an email should be sent.

**ScraperTask**

1. **Fetch + parse**: loads the product page and extracts the price.
2. **Store**: records at most one price per product per day in `price_history`.
3. **Evaluate**: compares today's price with the last 365 days. When a criterion fires, writes one `detections` row per interested user.

**NotifierTask**

4. **Send**: groups pending detections by recipient and sends the email.
5. **Mark**: stamps each delivered detection as sent.

The `detections` table is the only shared state between the tasks; neither references the other.

Two criteria are evaluated, in this order, once a product has at least 7 days of price history:

| Criterion | Fires when today's price is |
|---|---|
| Lowest price | below the minimum of the window |
| Lower bound | at or below the mean minus one standard deviation |

A user is notified again only if the price falls below the last price they were sent, or after 7 days.

---

## Stack

**Python 3.14**

| Layer | Choice |
|---|---|
| API | FastAPI |
| Contracts & configuration | Pydantic v2 + pydantic-settings |
| Persistence | SQLAlchemy 2.0 + PostgreSQL (psycopg 3) |
| Scheduling | APScheduler |
| Scraping | requests + BeautifulSoup |
| Auth | JWT + bcrypt |
| Email | smtplib (SMTP) |
| Container | Docker + Docker Compose |
| Tests | pytest |

All dependencies are pinned in `requirements.txt` and `requirements-dev.txt`.

---

## Getting started

### Requirements

- Python 3.14
- PostgreSQL
- A Gmail account with an app password ([how to create one](https://support.google.com/accounts/answer/185833); it requires [2-Step Verification](https://support.google.com/accounts/answer/185839)). The API runs without it, but the notification step of the daily job will fail.
- Docker, only if you want to run the API in a container.

### Setup (Windows)

```powershell
git clone https://github.com/fredericotl/AutoSearch.git
cd AutoSearch

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

Copy-Item .env.example .env      # fill in the values before starting
```

### Database

The schema is written by hand in [`sql/schema.sql`](./sql/schema.sql). The application does not create tables on startup, so this step comes before the first run:

```bash
createdb -U postgres autosearch
psql -U postgres -d autosearch -f sql/schema.sql
```

On Windows, the PostgreSQL binaries are in `C:\Program Files\PostgreSQL\<version>\bin` and may need to be added to `PATH`.

### Environment variables

Settings are loaded at import time, so the application will not start with a missing or incomplete `.env`.

| Variable | Purpose |
|---|---|
| `SQLALCHEMY_DATABASE_URL` | Database URL for the local run (`localhost`) |
| `SQLALCHEMY_DATABASE_URL_DOCKER` | Database URL used by the container (`host.docker.internal`) |
| `SECRET_KEY` | JWT signing key |
| `SENDER_EMAIL` | Gmail address that sends the notifications |
| `SENDER_PASSWORD` | Gmail app password, exactly 16 characters |
| `LOG_LEVEL` | Optional, defaults to `INFO` |
| `TIME_ZONE` | Optional, defaults to `America/Sao_Paulo` |

### First admin

Registration requires an invite, and only an admin can create one. The first admin is created from the terminal:

```bash
python -m app.workers.create_admin
```

### Run locally

```bash
uvicorn app.main:app --reload
```

Interactive API docs are available at `http://localhost:8000/docs`.

To run the daily round on demand, without waiting for the schedule:

```bash
python -m app.workers.cli
```

### Run with Docker

```bash
docker compose up -d
docker compose logs -f api
```

The API is available at `http://localhost:8001/docs`. The container uses the PostgreSQL instance on the host machine, the same one as the local run.

> [!WARNING]
> Do not run the local API and the container at the same time. Each one has its own scheduler, and both write to the same database.

### Registration

Every route outside `/auth` requires a token, so an account comes first. Accounts are created by invite:

```text
Admin   POST /auth/token     ──▶ admin token
        POST /admin/invites  ──▶ invite token, shared with the new user

User    POST /auth           ──▶ account, created with the invite token
        POST /auth/token     ──▶ user token
```

### Routes

#### Auth (no token)

| Method | Route | What it does |
|---|---|---|
| `POST` | `/auth` | Register a user with an invite token |
| `POST` | `/auth/token` | Get a JWT |

#### Admin (admin token)

| Method | Route | What it does |
|---|---|---|
| `POST` | `/admin/invites` | Create a single-use invite for an email|

#### User (user token)

| Method | Route | What it does |
|---|---|---|
| `GET` | `/user/` | Read your own data |
| `PUT` | `/user/password` | Change your password |
| `PUT` | `/user/email` | Change your email |

#### Products (user token)

| Method | Route | What it does |
|---|---|---|
| `GET` | `/products/` | List the products you follow, with today's price, lowest price and mean |
| `GET` | `/products/{id}` | Read one product with its prices |
| `POST` | `/products/` | Register and follow a product |
| `DELETE` | `/products/{id}` | Stop following a product |
| `POST` | `/products/{id}/save-price` | Capture today's price on demand |

---

## Architecture

Each layer owns one concern and depends only downward. Business rules live in `services/`, allowing the API and background workers to reuse the same logic.

| Module | Responsibility                                                                      |
|---|-------------------------------------------------------------------------------------|
| `api/` | HTTP routes: validate input, delegate, and translate domain errors into responses   |
| `schemas/` | Pydantic contracts for API input/output and layer boundaries                        |
| `models/` | ORM entities, columns, relationships, and constraints                               |
| `services/` | Business rules shared by the API and workers                                        |
| `scraper/` | Fetching and parsing product pages, with one implementation per site                |
| `notifier/` | Message composition and delivery through an external channel                        |
| `workers/` | Scheduled scraping, notification tasks and the command that creates the first admin |
| `db/` | Engine, session, and declarative base                                               |
| `core/` | Configuration, clock, logging, security, and domain exceptions                      |
| `main.py` | Composition: routers and the daily round                                            |

```text
api      ──▶ services ──▶ models / db
workers  ──▶ services
workers  ──▶ notifier
services ──▶ scraper
```

For the detailed boundaries and rationale, see [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Design decisions

Three decisions are especially relevant:

**Price detection is computed from history, not a stored aggregate.**  
The comparison window slides, so yesterday's minimum can leave the window without a new write. Recomputing an indexed slice keeps the result correct and is negligible at this scale.
([ADR-014](./ARCHITECTURE.md#adr-014-the-price-window-is-computed-from-history))

**The notification criterion is derived from the data, not configured per user.**  
The criterion is a business conclusion, not a user preference. The amount of history determines which criteria are *computable*.
([ADR-016](./ARCHITECTURE.md#adr-016-the-notification-criterion-is-derived-from-the-data))

**Detections are handed between workers through a table, not memory.**  
The scraping task writes detections when the criterion fires; the notification task reads unsent rows and marks them after delivery. This survives restarts and keeps the tasks decoupled.
([ADR-017](./ARCHITECTURE.md#adr-017-detections-are-handed-over-through-a-table))

All decisions, including their context and trade-offs, are documented in [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Development

### Tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

The tests create their own schema on in-memory SQLite, so they do not need PostgreSQL.

The suite mirrors `app/`, one folder per layer:

| Folder | What it covers |
|---|---|
| `test_services/` | Business rules: price window and criteria, repeated-notification rule, invites, product lifecycle |
| `test_api/` | Routes through FastAPI's `TestClient`: status codes, authentication, invite registration, price reads |
| `test_scraper/` | Price parsing on minimal HTML, including unavailable products and carousel prices |
| `test_notifier/` | Email subject and body, and translation of SMTP errors into domain errors |
| `test_workers/` | A failing product does not abort the round, and the notifier runs even when scraping fails |
| `test_core/`, `test_schemas/` | Clock, settings, tokens and input validation |

### Keeping the schema in sync

The schema is described twice, in `sql/schema.sql` and in `app/models/`. To compare them, create a throwaway database from the models with `Base.metadata.create_all`, then diff both schemas:

```bash
pg_dump -U postgres --schema-only autosearch > from_sql.sql
pg_dump -U postgres --schema-only <throwaway_db> > from_models.sql
diff from_sql.sql from_models.sql
```

`text` versus `character varying` is the only expected difference.

### Inspecting errors

Failures from the daily round are recorded in the `errors` table. `source` tells where they came from (`scraper` or `notifier`), and `error_type` names the domain exception. The most recent ones:

```sql
SELECT captured_at, source, error_type, product_id, user_id, message
FROM errors
ORDER BY captured_at DESC
LIMIT 20;
```

Programming errors are not stored there. They go to `logs/app.log`.

---

## Status and limitations

The project runs end to end from a clean clone. The limitations below are intentional and known.

**Scoped out on purpose**

- **One site supported.** Amazon is the only active scraper. A Mercado Livre scraper exists but is disabled, because the site requires a browser-based approach. The scraper is structured so another site can be added as a new implementation rather than a rewrite.
- **The scheduler runs inside the API process.** It is adequate for local execution and is the first component to change before deployment.
- **Login is not throttled.** The API is intended for local use, not public exposure.