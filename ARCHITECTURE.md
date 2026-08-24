# Architecture

AutoSearch is a price monitoring backend: a REST API registers products and users, and a daily
job captures the price of each product, stores the observation, and sends an email when the price
reaches the lowest value in the recorded history.

This document describes the code organization, its boundaries, and the reasons behind each decision. It does not describe future work.

## Flow

The daily round consists of two independent tasks, chained at composition time:

```
ScraperTask     fetch → parse → write to price_history → evaluate criterion → write to detections
NotifierTask    read pending detections → group by recipient → send → mark as sent
```

The tasks do not reference each other. The `detections` table is their only shared state, and `main.py` defines their order.

## Codemap

```
app/
├── api/              # HTTP layer (routes)
│   ├── auth.py       # registration + token issuance
│   ├── product.py    # product CRUD + API price capture
│   └── users.py      # the caller's own data and changes
├── schemas/          # Data contracts (Pydantic)
│   ├── product.py    # CreateProduct, ProductResponse, ProductPriceResponse, ProductToScrape
│   ├── user.py       # CreateUser, Token, UserResponse, ChangePassword, ChangeEmail, ViewerRef
│   ├── notifier.py   # Criteria, DetectionNotifyByUser, NotifierInput, ProductToNotify, PriceWindowStats
│   └── error.py      # ErrorSource (Enum), CreateError
├── models/           # Persistence (ORM)
│   ├── associations.py  # association tables
│   ├── product.py
│   ├── user.py
│   ├── pricehistory.py  # PriceHistory
│   ├── detection.py     # Detection — detection log
│   └── error.py         # Error — system-wide error log
├── services/         # Business rules
│   ├── product_service.py    # product CRUD and lifecycle
│   ├── price_service.py      # price capture + criterion evaluation
│   ├── detection_service.py  # writing, reading and marking detections
│   ├── error_service.py
│   └── user_service.py
├── scraper/          # External adapter — fetch + parse
│   ├── base.py       # Scraper (ABC): shared get_soup, abstract parse, get_price template
│   ├── amazon_scraper.py
│   └── factory.py
├── notifier/         # External adapter — notification delivery
│   ├── base.py           # Notifier (ABC) — the axis of variation is the channel
│   └── email_notifier.py # EmailNotifier (SMTP)
├── db/               # Connection and session
│   └── session.py
├── core/             # Configuration and cross-cutting concerns
│   ├── config.py     # Settings (pydantic-settings)
│   ├── security.py
│   └── exceptions.py  # domain exceptions, grouped into two families
├── workers/          # Background tasks
│   ├── scraper_task.py    # ScraperTask — scraping + detection
│   ├── notifier_task.py   # NotifierTask — delivery of pending detections
│   └── scheduler.py       # TaskScheduler — scheduling wrapper (APScheduler)
└── main.py           # create_all, composition of the daily round, lifespan
```

## Responsibilities

| Module | Responsibility | Key idea |
|---|---|---|
| `api/` | Receive the request, validate input, delegate to a service, return the right status code | Thin edge: translates domain exceptions into `HTTPException`; services remain unaware of HTTP. Routes should stay small; business logic belongs in services. |
| `schemas/` | Define what enters and leaves the API, and what crosses a boundary between layers | Public contract ≠ internal structure: `UserResponse` exposes neither `hashed_password` nor `role`. Optional input fields require corresponding optional output fields. |
| `models/` | Map tables, columns, relationships and constraints | Describes how data is stored, not how it travels. `nullable=False` is defense in depth because the API is not the only path to the database. |
| `services/` | Business logic: create products, capture and persist prices, evaluate criteria, and record detections and errors. | Callable by both the API and the workers. Domain constants live here |
| `scraper/` | Fetch HTML and extract a price, translating library failures into domain exceptions | Fixed boundary: fetching is shared; parsing varies by site. |
| `notifier/` | Compose and deliver a message over an external channel | Receives a ready `NotifierInput`; it does not query the database, choose recipients, or record errors. |
| `db/` | Engine, session, declarative `Base`, the `get_db` dependency | Isolated infrastructure. Replacing SQLite with Postgres should require minimal changes elsewhere. |
| `workers/` | Background work that must not block HTTP requests | Temporal decoupling. Reuses `services/` instead of duplicating logic. This layer decides whether a failure affects one item or the whole round. |
| `core/` | Configuration, security, and the domain exception vocabulary | Cross-cutting concerns consumed by every layer and dependent on none. |
| `main.py` | Create the app, register routers, create the schema, compose the round | Composition only, including task ordering. |

Three conventions that cut across the table:

- **Closed sets of values use `String` in the database and `Enum` in the schema** (`User.role`,
  `Detection.criteria`, `Error.source`). Validation lives at the edge and a new value needs no table
  change; the accepted cost is that the database does not validate on its own.
- **Relationships between `User` and `Product` declare `foreign_keys` explicitly.** There are two
  paths between them, and without it SQLAlchemy cannot choose and fails at initialization.
- **Environment configuration is a single `Settings(BaseSettings)` read from `.env`.** Domain rules
  do not belong there. It is instantiated at import time, so any module that depends on it requires
  a valid `.env`.

## Dependencies and invariants

```
api      ──▶ services ──▶ models / db
workers  ──▶ services
workers  ──▶ notifier
services ──▶ scraper
main.py  ──▶ workers
```

The rules below are stated as absences — they describe what must not appear in the code:

- **`services/` never imports from `api/`.** The reverse direction is inverted coupling.
- **`workers/` does not know about tables.** No model imports, no queries. Domain rules belong to
  the service; task orchestration belongs to the worker.
- **`workers/` does not know about external libraries.** `requests` and `smtplib` never appear
  there — failures arrive already translated into domain exceptions.
- **No service that receives `db` calls `commit`.** The transaction belongs to whoever opened the
  session.
- **Nothing from the ORM crosses a session boundary.** What leaves a session block is a Pydantic
  snapshot, not a mapped instance.
- **Log tables declare no `relationship`.** `PriceHistory`, `Detection` and `Error` are read through
  explicit queries, joined when context is needed — a relationship on a log table is an invitation
  to lazy loading.
- **Imports between services target the module, never the package facade.** The facade
  (`__init__.py`) exists for consumers outside the package; using it from the inside creates a
  cycle. Private functions are not re-exported.

## Decisions

Format: context → choice → reason. The numbering has gaps: decisions covering naming and
organization conventions were dropped as noise, and what survived of them became a note on the
corresponding layer. Numbers are never reused.

### ADR-003: authorization belongs to the edge — declared in core/, applied in api/

"Admin" is a permission level, not a resource: `require_admin` lives in `core/security.py` and routes
declare it through `Depends`. Workers call services directly and go through no access control —
authorization exists for external actors, and a worker is not one.

### ADR-007: a product is public — it survives without an owner and is deleted without viewers

The user↔product link is a plain associative `Table` with a composite primary key and no metadata,
kept in `models/associations.py` — a neutral file that avoids cross-imports between `product.py` and
`user.py`. On top of that link, a product survives without an owner (`owner_id` nullable,
`ondelete="SET NULL"`) and is deleted when it loses its last viewer.

SQLite does not enforce `ON DELETE` without a per-connection PRAGMA, so `remove_product` deletes the
detections **before** the product, in the same transaction. Order matters: with the foreign key
enforced, deleting the product first would trigger `SET NULL` and the filter on `product_id` would
match nothing.

### ADR-010: one event, two contracts — private logic plus per-caller wrappers

Capturing a price has two consumers with opposite needs. For the API, finding no price is a *result*
— 200 with `status="no_price_found"`. For the worker, it is an *exception*: inside a loop, the value
only matters when it exists. The obvious alternative, duplicating the logic per caller, would leave
capture with two owners.

So the real logic lives in `_capture_price` (private) and two thin wrappers sit on top: one returns
the response as is, the other raises `PriceNotFound` and returns the price when there is one. The
leading underscore is not decoration — it marks the function as absent from the package facade, so
consumers pick one of the two contracts and never the one in between.

A *fetch* failure raises before any write and therefore produces no row in `price_history`, while
*parse* still returns `None`. That is what gives `price=NULL` a single meaning: the page was reached
and no price was found.

### ADR-011: one service per lifecycle, not per entity

Product CRUD and price capture deal with the same entity but have different dependencies and
rhythms — the first answers a request and only talks to the database, the second depends on an
external network and runs on a schedule. The boundary reflects that difference and anticipates the
cut that queue-based scraping will require: when capture becomes a message, the file that changes is
already isolated. `detection_service` was later born from the same criterion.

### ADR-012: get_product raises ProductNotFound, and the resource is resolved once at the edge

The lookup raises instead of returning `None`, and resolution happens once per context rather than at
every step of the chain. A `None` meaning "does not exist" forces every caller to check, and
forgetting is silent, so the error surfaces far from its cause.

This does not prohibit `None` as a return value: `PriceWindowStats.minimum = None` ("not enough
history") and `evaluate_price_criteria → None` ("no criterion fired") are legitimate business
answers. The rule is about a `None` that disguises an error. It also does not require passing whole
objects around — `get_price_window_stats` takes a `product_id: int`, because that is all the function needs.

### ADR-014: sliding window computed in the query, without an aggregate table

`get_price_window_stats` returns `PriceWindowStats(minimum, count)` from a query using `func.min` and
`func.count`, scoped to a 365-day window that excludes the current day. The decision itself is
`evaluate_price_criteria`, a pure function. The reasons are:

1. **A sliding window invalidates an incremental aggregate:** The values change with no new write —
   the clock alone is enough. `min` and `max` are precisely the aggregates that do not survive the
   removal of data points.
2. **The scale does not justify it:** With an index on `product_id`, the aggregate walks a few
   hundred rows per year.
3. **Excluding the current day makes detection independent of the writer:** The API writes, the
   worker writes; the cut in the `WHERE` clause applies to both.
4. **Pure core, imperative shell:** I/O in the query, policy testable with three numbers.

`func.count(PriceHistory.price)` counts prices collected, not attempts made. The comparison uses a
strict `<`: with `<=`, a product sitting at its minimum would fire every single day.

### ADR-015: the transaction belongs to whoever opens the session

No `services/` function that receives `db: Session` calls `commit`. Only the caller that sees the
whole unit of work knows where it begins and ends — a leaf function never does, and by committing it
decides on behalf of every caller. Beyond that, `commit` is not local: it writes everything pending
in the session, including what the caller did not consider ready. Corollary: `commit` goes on the
successful path and in the `except` that records the error, never in `finally`, which is for
releasing resources. Accepted cost: a caller that forgets to commit loses the work silently.

### ADR-016: the notification criterion is derived from the data, not configured

Persisting `criteria` as a column on `Product`, on the link table, or on `User` was evaluated and
dropped. The criterion is not a preference, it is a conclusion: `evaluate_price_criteria` returns
`Criteria | None`. Defining what counts as "cheap" is not the user's job — the user wants to know
that the price is low, and which evidence supports that is a business rule. The amount of history
does not select the criterion; it determines which criteria are *computable*. Criteria are checked
in order with an early return on the first that fires, which makes the order of the code the
precedence rule. `criteria` does go back to the database, in `Detection` — but as a recorded fact,
not as configuration.

### ADR-017: detections delivered through a table, with fan-out at detection time

The scraping run writes one row per (product, user) at the moment the criterion fires; the
notification run queries `WHERE sent_at IS NULL`, groups by recipient, sends, and marks exactly the
`detection_id` values that were in the email. The reasons are:

1. **Record vs. log:** `product_viewers` is a *record*: one row per pair, permanently. `detections`
   is a *log*: one row per pair **per event**.
2. **Fan-out at detection, not at delivery:** Doing it at delivery would require two tables to get
   per-user idempotency; doing it at detection, one is enough.
3. **The table removes the coupling:** Neither worker references the other, neither holds state in
   memory, and a restart between the two runs loses nothing.
4. **`sent_at` answers two questions:** what is left to send, and what was already
   sent to whom.

The row is not deleted after delivery. The chosen guarantee is *at least once*: marking happens
after a successful send.

### ADR-018: errors — translate at the boundary, classify by action, decide in orchestration, record in one log

Four responsibilities, one per layer: **Translate** (`scraper/`, `notifier/`): catch the library
exception and convert it into a domain exception with `raise X(...) from e`, preserving both the
traceback and the cause. **Classify** (`core/exceptions.py`): exceptions named after the action they
demand rather than the library that raised them, in two families with a common base — `ScraperFail`
and `NotifierFail`. **Decide** (`workers/`): catch by tuple and map to an action — record and
continue, or record and abort. **Record** (`models/error.py`): a single `errors` table for the whole
system, with `source` separating origins.

`SenderNotAuthenticated` says "fix the credential"; `SMTPAuthError` only repeats what the library
already said. The common base is a safety net: an exception someone forgets to list degrades to
"recorded and skipped". The `except` clauses always run from specific to generic — `SMTPException`
inherits from `OSError`, so an `except OSError` at the top would swallow every specific one.

### ADR-019: nothing from the ORM crosses a session boundary

Two complementary changes: the service explicitly loads (`selectinload(Product.viewers)`), and the
worker converts at the boundary, inside the block where the session is still alive, turning each
`Product` into a `ProductToScrape` (Pydantic, `from_attributes=True`). "Detached" is not the problem;
"detached and not loaded" is. The two changes answer different questions: `selectinload` answers how
many queries this costs, the conversion answers what crosses the boundary. And the conversion *is*
the loading — with `from_attributes=True`, validating means reading the attributes. `selectinload`
rather than `joinedload` because, for a collection, `joinedload` multiplies parent rows and requires
deduplication.

### ADR-020: in workers/, the task is separate from the scheduling

`ScraperTask` and `NotifierTask` expose `run()` and do not know that cron exists; `TaskScheduler` is
a thin wrapper over `BackgroundScheduler` and does not know what it is scheduling; the composition —
scraper and then notifier, once a day — happens in `main.py`. This makes `run()` callable without
touching a scheduler, and makes the scheduling library a replaceable detail. Of the three ways
to chain the tasks, this is the only one that keeps both workers free of references to each other
*and* free of any dependency on the scraper finishing in time. The notifier runs in a `finally`: if
the scraper blows up, detections pending from earlier rounds are still delivered.

### ADR-021: the schema is born from the models, with no migrations in the MVP

`Base.metadata.create_all` is called in the `lifespan`, and the models are the single source of
truth for the schema. `create_all` and a migration tool do not coexist: with `create_all` running on
an empty database, every migration that issues `create_table` collides with it. Keeping both means,
in practice, picking one and leaving the other as dead weight.

Accepted cost, and the thing that keeps this decision valid: `create_all` **does not alter an
existing table** — a new column on a model never reaches the database and raises nothing at boot; it
breaks on the first query. That is only acceptable while the database is disposable. The triggers to
revisit are the first data that cannot be recreated, a move to Postgres, or a second person on the
project. And the correct order, when that happens, is: empty database first, migrations second,
`create_all` never again.

## Known limits

Consequences of the current design, not pending work:

- **`ON DELETE` is inert under SQLite.** The constraints are declared and only take effect on
  Postgres; until then, the deletion order inside the service is what preserves integrity (ADR-007).
- **The scheduler lives inside the API process.** With more than one web worker there would be one
  scheduler per process. The separation set up in ADR-020 is what makes that cut cheap when it is
  needed.
- **`captured_at` is UTC while day-based cuts use local dates.** The three-hour gap between the two
  affects which day a late-night capture belongs to.
- **The scraper treats a block served with HTTP 200 as a missing price.** The hook exists in
  `base.py`, but no concrete scraper implements it.
