# Architecture

AutoSearch is a price monitoring backend. A REST API registers users and products, and a daily job captures the price of each product, stores it, and emails the users who follow that product when the price is low compared with its recent history.

This document explains how the code is organized and why. Project status, setup and known gaps are in the [README](./README.md).

## Layers at a glance

| Folder | Responsibility | What decides that code lives here |
|---|---|---|
| `api/` | Receive and answer HTTP requests | Thin edge. It turns domain exceptions into `HTTPException` |
| `schemas/` | Input, output and cross-layer contracts | Anything that crosses a boundary. A closed vocabulary lives with the layer that produces it |
| `models/` | Tables, columns and relationships | How data is stored. Log tables declare no `relationship` |
| `services/` | Business rules and decisions | Callable by the API and by workers. It knows nothing about HTTP |
| `scraper/` | Fetch the page and extract the price | External adapter. Fetching is shared, parsing changes per site |
| `notifier/` | Build and deliver the message | External adapter. Each subclass is a delivery channel |
| `db/` | Engine, session, `Base`, `get_db` | Isolated infrastructure. The database URL arrives ready from settings |
| `workers/` | Work that runs outside a request | Orchestrates services. It imports no models, writes no queries and never touches `requests` or `smtplib` |
| `core/` | Settings, clock, logging, security, exceptions | One source per cross-cutting question. It never queries the database or imports from `app/` |
| `main.py` | Build the app and the daily round | Assembly only |

## Flow

The daily round has two tasks, chained at composition time:

```
ScraperTask     fetch → parse → write to price_history → evaluate criterion → write to detections
NotifierTask    read pending detections → group by recipient → send → mark as sent
```

The round has two entry points: `main.py` schedules it daily, and `workers/cli.py` runs it on demand.

## Folder structure

```
app/
├── api/        HTTP layer, one router per resource
├── schemas/    Pydantic contracts and closed vocabularies
├── models/     ORM entities
├── services/   business rules
├── scraper/    page fetching and price parsing
├── notifier/   message delivery
├── db/         connection and session
├── core/       cross-cutting concerns
├── workers/    tasks and scheduling
└── main.py     entry point

sql/            hand-written PostgreSQL schema
tests/          mirrors app/ (left out of the Docker image)
```

At the root: pinned `requirements.txt` and `requirements-dev.txt`, `Dockerfile`, `docker-compose.yml` and `pytest.ini`. The `.env` file stays out of git and out of the image.

## Dependencies

```
api      ──▶ services ──▶ models ──▶ db
workers  ──▶ services ──▶ scraper
workers  ──▶ notifier
main.py  ──▶ workers

every layer ──▶ core
every layer ──▶ schemas
```

The arrows only point down. `services/` never imports from `api/`, since that would make business rules depend on the HTTP layer.

### Package facades

Each package in `app/` exposes its public names through `__init__.py`.

1. The facade exposes what crosses the package boundary, and nothing else.
2. Code inside a package imports by module, never through its own facade. Going through the facade closes a cycle with `__init__.py`.
3. A public name belongs to one facade. Repeated names get aliases (the four `router` objects become `auth_router`, `user_router`, `product_router` and `admin_router`).

4. Private functions (leading `_`) never enter a facade.

## Decisions

Each decision states what was chosen and why. The numbering has gaps because early decisions about naming and organization were folded into the sections above. Numbers are never reused.

### ADR-003: authorization belongs to the edge

`get_admin` lives in `core/security.py` and routes declare it through `Depends`. Workers call services directly and skip access control, since authorization exists for external actors. Code that queried the database moved from `core/` to `services/`, and security functions receive plain values (`username`, `user_id`, `user_role`) instead of the `User` entity.

### ADR-007: a product is public

The user↔product link is a plain association table with a composite key and no extra columns. A product belongs to the catalog: it survives when its owner leaves (`owner_id` is nullable with `ON DELETE SET NULL`) and is deleted when it loses its last viewer.

### ADR-010: one event, two contracts

Capturing a price has two callers with opposite needs. For the API, finding no price is a result (200 with `status="no_price_found"`). For the worker, it is an exception. The logic lives once in `_capture_price`, and two thin wrappers expose the two contracts:

```
_capture_price
 ├── save_product_price_api        → returns a status
 └── save_product_price_scheduler  → raises PriceNotFound
```

Cost: `price = NULL` exists in the history, with a single meaning ("the page was reached and no price was found"). Every consumer of prices filters it out.

### ADR-011: one service per lifecycle, not per entity

Two pairs of services handle the same entity at different moments: `product_service` and `price_service`, and `user_service` and `auth_service`. Product CRUD answers a request and only talks to the database, while price capture depends on the network and runs on a schedule. Identity runs before a token exists, while profile changes run after.

### ADR-012: lookups raise, and the resource is resolved once at the edge

`get_product` raises `ProductNotFound` instead of returning `None`. A `None` that means "does not exist" forces every caller to check, and forgetting fails silently far from the cause. `None` is still valid when it is a business answer, such as `evaluate_price_criteria` returning `None` when no criterion fired.

### ADR-014: the price window is computed from history

There is no aggregate table. A sliding window changes when the clock moves, even with no new write, and `min` does not survive the removal of old points. “The window length is a domain constant (WINDOW_OF_DAYS, 365 days).”

Detection excludes the current day, so it gives the same answer whether the API or the worker wrote today's price. The API read keeps the current day, because the screen compares today's price with the window that contains it.

### ADR-015: the transaction belongs to whoever opens the session

Only the caller that sees the whole unit of work knows where it starts and ends, and `commit` writes everything pending in the session. So `api/` and `workers/` commit, and services never do. `commit` goes on the success path and in the `except` that records an error, never in `finally`. Cost: a caller that forgets to commit loses the work silently.

### ADR-016: the notification criterion is derived from the data

Users do not configure what "cheap" means, because they do not have the price series. The system evaluates the criteria it can compute and returns the first one that fires:

1. `LOWEST_PRICE`: today's price is below the window minimum.
2. `LOWER_BOUND`: today's price is at or below the mean minus one standard deviation.

Both require 7 days of price history in the window. The order of the checks is the precedence rule. The criterion is stored in `detections` as a record of what happened.

### ADR-017: detections are handed over through a table

The scraper writes one row per (product, user) when a criterion fires. The notifier reads `WHERE sent_at IS NULL`, groups by recipient, sends, and marks the rows it sent.

```
ScraperTask ──writes──► [detections] ◄──reads/marks── NotifierTask
                          sent_at NULL = pending
```

Fan-out happens at detection time, which freezes who should be notified at the moment the price was valid. The table is the only state the two tasks share, so neither references the other and a restart between them loses nothing. Cost: delivery is at least once, since marking happens after a successful send.

### ADR-018: errors are translated, classified, decided and recorded in different layers

```
scraper/ notifier/   translate   raise X(f"{type(e).__name__}: {e}") from e
core/exceptions.py   classify    ScraperFail | NotifierFail
workers/             decide      skip the item or abort the round
models/error.py      record      one errors table, with a source column
```

Exceptions are named after the action they demand (`SenderNotAuthenticated` means "fix the credential"). A common base per family is a safety net for exceptions nobody listed. The `errors` table records operational failures only. Programming errors go to the log. Cost: a `TypeError` inside the scraper loop still costs the whole round.

### ADR-019: nothing from the ORM crosses a session boundary

The service loads explicitly (`selectinload`), and the worker converts each entity into a Pydantic schema (`from_attributes=True`) while the session is still open. A detached object is fine once it has been loaded. The risk is an object that is detached and not loaded, and converting at the boundary forces the load while it is still possible.

### ADR-020: a task is separate from its schedule

`ScraperTask` and `NotifierTask` expose `run()` and know nothing about cron. `TasksRound` chains them, and `TaskScheduler` is a thin wrapper over APScheduler. A task can be tested without waiting for a time of day, and the scheduling library is a replaceable detail.

In `TasksRound`, the notifier runs in `finally`, so detections already written are sent even if scraping fails halfway. `misfire_grace_time` is set in hours: running a few hours late costs almost nothing, while skipping a run leaves a gap in the series.

### ADR-022: modules emit logs, the entry point configures them

All logging setup lives in `core/logging_setup.py`, and `setup_logging()` is idempotent. Modules only call `logging.getLogger(__name__)`. Handlers are attached to named loggers (`app` and `apscheduler`), never to the root, so a library reaches the log file only when it is named. `apscheduler` was added after it reported a skipped round to a logger with no handler.

### ADR-023: one clock, São Paulo time, stored naive

`core/clock.py` exposes `now()`, which reads `TIME_ZONE` from settings and returns a naive datetime. Every timestamp column uses `default=clock.now`, and the schema declares no time defaults. Before this, the database wrote UTC and the log used the machine's zone, which shifted the detection window by three hours. `core/security.py` keeps UTC, because a JWT `exp` is UTC by specification.

Columns are `TIMESTAMP` without time zone. A `timestamptz` column would reinterpret the naive value using the session time zone, so adopting it requires changing the clock first.

### ADR-024: the price window is an object with alternative constructors

The window, its minimum, sum and deviation are always read together, and every criterion is a rule about them. `PriceWindow` groups them, with three entry points:

```
from_history(db, product_id) ──► from_prices(list[int]) ──► __init__(4 values)
      (the only I/O)               (pure arithmetic)          (stores only)
```

Tests enter through `from_prices` with a list of integers and no database. The deviation is the sample one (`stdev`), since the window is a sample of the product's prices. Cost: an empty window is constructible and produces `None` attributes, so each method guards against it.

### ADR-025: the database lives outside the container

Context. The `Dockerfile` and `docker-compose.yml` were generated with an AI assistant. I reviewed them and ran the container to check that the API works and reads the same data as the local run.

Decision. PostgreSQL runs on the host machine, outside the container. Compose injects `.env` into the container and overrides the database URL with an address that points to the host (`host.docker.internal`).

Why. With the database outside, the local run and the container share one set of data. Environment variables take priority over `.env` in `pydantic-settings`, so the code has no branch for the two cases.

Cost. Each run has its own scheduler and both write to the same database, so the local run and the container must not run at the same time.

### ADR-026: the last notified price is the new reference

A product that stays cheap would fire every day. A new detection is written only if the price is below the last price already sent to that user, or if 7 days have passed since that send. The reference is per (product, user), because two users of the same product can be at different points of the series. A fixed cooldown was rejected because it would silence a strong drop. Cost: the rule reads only detections already sent, so two rounds on the same day, before delivery, escape it.

### ADR-027: PostgreSQL with a hand-written schema

The schema lives in `sql/schema.sql`, written by hand. The app does not create tables at startup, and there is no migration tool. I write the DDL myself because that is where I learn the database, and Alembic is out of proportion for a project this size. This replaced the MVP approach of calling `create_all` at startup, which was only acceptable while the database was disposable.

Cost: the schema is described twice, in `sql/schema.sql` and in `app/models/`, and nothing keeps them in sync automatically. Tests are the exception and create the schema with `create_all` on in-memory SQLite.


### ADR-033: registration requires an invite

Registration needs an invite, created by an admin at `POST /admin/invites`. The invite is bound to one email and one role, expires after one day, and can be used once. The database stores only the SHA-256 hash of the token. Without this control, the API could not be exposed on the network.

Cost: the first admin cannot be created through the API. It is created from the terminal (`python -m app.workers.create_admin`), on a machine with access to the database.

## Known limits

- The scheduler runs inside the API process. More than one web worker would mean more than one scheduler. ADR-020 keeps that split cheap when it is needed.
- A block page served with HTTP 200 is read as a missing price. The hook (`_is_blocked`) exists in the scraper base, but no site implements it.
