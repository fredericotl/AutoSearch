# AutoSearch

A Python/FastAPI backend that tracks daily prices for registered products and emails users when a price reaches the lowest value in the recorded history.

A price has little meaning without historical context. AutoSearch builds that history automatically.

*Personal project focused on backend architecture. Design decisions are documented in [`ARCHITECTURE.md`](./ARCHITECTURE.md).*

---

## How it works

A scheduled job runs once a day. For each registered product, it captures the current price, stores it, and evaluates whether an email should be sent.

**ScraperTask**

1. **Fetch + parse** — loads the product page and extracts the price.
2. **Store** — records the captured price in `price_history`.
3. **Evaluate** — when the criterion fires, writes one `detections` row per interested user.

**NotifierTask**

4. **Send** — groups pending detections by recipient and sends the email.
5. **Mark** — stamps each delivered detection as sent.

The `detections` table is the only shared state between the tasks; neither references the other. See [Design decisions](#design-decisions) for how a price is evaluated.

---

## Stack

**Python 3.13**

| Layer | Choice |
|---|---|
| API | FastAPI |
| Contracts & configuration | Pydantic v2 + pydantic-settings |
| Persistence | SQLAlchemy 2.0 + SQLite |
| Scheduling | APScheduler |
| Scraping | requests + BeautifulSoup |
| Auth | JWT + bcrypt |
| Email | smtplib (SMTP) |

All dependencies are pinned in `requirements.txt`.

---

## Getting started

### Requirements

- Python 3.13
- A Gmail account with an app password. The API runs without it, but the notification step of the daily job will fail.

### Setup

```bash
git clone https://github.com/fredericotl/AutoSearch.git
cd AutoSearch

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate

pip install -r requirements.txt

cp .env.example .env             # fill in the values before starting

uvicorn app.main:app --reload
```

The SQLite file and its tables are created on first startup; no migration step is required.

### Environment variables

Copy `.env.example` to `.env` and fill in the required values. Settings are loaded at import time, so the application will not start with a missing or incomplete `.env`.

### First requests

Interactive API docs are available at `http://localhost:8000/docs`.

The order matters: register a user and request a token, then register a product. Price capture requires an existing product.

---

## Architecture

Each layer owns one concern and depends only downward. Business rules live in `services/`, allowing the API and background workers to reuse the same logic.

| Module | Responsibility |
|---|---|
| `api/` | HTTP routes: validate input, delegate, and translate domain errors into responses |
| `schemas/` | Pydantic contracts for API input/output and layer boundaries |
| `models/` | ORM entities, columns, relationships, and constraints |
| `services/` | Business rules shared by the API and workers |
| `scraper/` | Fetching and parsing product pages, with one implementation per site |
| `notifier/` | Message composition and delivery through an external channel |
| `workers/` | Scheduled scraping and notification tasks |
| `db/` | Engine, session, and declarative base |
| `core/` | Configuration, security, and domain exceptions |
| `main.py` | Composition: routers, schema creation, and the daily round |

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
([ADR-014](./ARCHITECTURE.md#adr-014-sliding-window-computed-in-the-query-without-an-aggregate-table))

**The notification criterion is derived from the data, not configured per user.**  
The criterion is a business conclusion, not a user preference. The amount of history determines which criteria are *computable*.
([ADR-016](./ARCHITECTURE.md#adr-016-the-notification-criterion-is-derived-from-the-data-not-configured))

**Detections are handed between workers through a table, not memory.**  
The scraping task writes detections when the criterion fires; the notification task reads unsent rows and marks them after delivery. This survives restarts and keeps the tasks decoupled.
([ADR-017](./ARCHITECTURE.md#adr-017-detections-delivered-through-a-table-with-fan-out-at-detection-time))

All decisions, including their context and trade-offs, are documented in [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Status and limitations

The project runs end to end from a clean clone. The limitations below are intentional and known.

**Scoped out on purpose**

- **One site supported.** The scraper is structured so another site can be added as a new implementation rather than a rewrite.
- **SQLite, with the scheduler inside the API process.** Both are adequate for local execution and are the first components to change before deployment.
- **Registration is open and unthrottled.** The API is intended for local use, not public exposure.

**Known gaps**

- No automated tests yet.
