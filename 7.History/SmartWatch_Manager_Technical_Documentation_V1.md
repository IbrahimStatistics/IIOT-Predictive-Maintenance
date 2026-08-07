# SmartWatch Manager — Technical Documentation
### Scripts, Architecture, and Technology Stack (as of end of Phase 3 core build)

---

## 1. System Overview

SmartWatch Manager's backend is built as a chain of independent, single-purpose components that pass data through well-defined interfaces (MQTT topics, a JSON schema, a database schema, a REST API). This document explains each script, what it's responsible for, and exactly how data flows between them.

```
┌──────────────┐    ┌──────────────────┐    ┌─────────┐    ┌──────────────┐    ┌───────────────┐    ┌─────────┐
│ MAFAULDA     │───▶│ loader.py        │───▶│ sensor_ │───▶│ Mosquitto    │───▶│ consumer.py    │───▶│ Timescale│
│ dataset      │    │ (extraction)     │    │simulator│    │ (MQTT broker)│    │ (async writer) │    │ DB       │
│ (.mat files) │    │                  │    │  .py    │    │              │    │                │    │          │
└──────────────┘    └──────────────────┘    └─────────┘    └──────────────┘    └────────────────┘    └────┬────┘
                                                                                                             │
                                                                                                             ▼
                                                                                                     ┌────────────┐
                                                                                                     │  main.py   │
                                                                                                     │ (FastAPI)  │
                                                                                                     │ + db.py    │
                                                                                                     │ + auth.py  │
                                                                                                     │ + config.py│
                                                                                                     └────────────┘
```

Each arrow represents a real, verified handoff — every stage has been independently tested and confirmed working with live data before moving to the next.

---

## 2. Directory Structure

```
Backend/
├── loader/
│   └── loader.py
├── simulator/
│   └── sensor_simulator.py
├── consumer/
│   └── consumer.py
└── api/
    ├── main.py
    ├── db.py
    ├── auth.py
    └── config.py
```

Each folder is a self-contained unit with a single responsibility, connected only through external interfaces (MQTT, HTTP, SQL) — not direct Python imports across folders, except `simulator.py` importing `loader.py` directly (the one intentional exception, since the simulator needs the loader's extraction logic at the source-array level).

---

## 3. Script-by-Script Breakdown

### 3.1 `loader/loader.py` — Dataset Extraction Layer

**Purpose:** Read raw motor sensor recordings out of the MAFAULDA dataset's native file format and return clean, ready-to-use numpy arrays.

**Why it exists:** The dataset ships as MATLAB v7.3 files, which are actually HDF5 files internally. MATLAB stores struct fields as *object references* (pointers) rather than raw arrays — meaning any consumer of this data must dereference those pointers correctly to get real numbers. This script encapsulates that entire process once, so nothing downstream ever has to deal with HDF5 internals directly.

**Key function:**
```python
load_signal(health_condition, torque_level, channel, repetition=0, file_suffix='R1') -> np.ndarray
```
- `health_condition`: which motor condition to load (`'rs'` = healthy, `'r1b'`–`'r4b'` = 1–4 broken rotor bars)
- `torque_level`: load level, `'torque05'` through `'torque40'` (0.5–4.0 Nm)
- `channel`: which signal, e.g. `'Ia'`, `'Vib_axial'`
- `repetition`: which of the 10 recorded repetitions (0–9)

**What it does internally:**
1. Builds the correct filename from the condition (e.g. `struct_rs_R1.mat`)
2. Opens the file with `h5py` (not `scipy.io.loadmat`, which cannot handle v7.3 files)
3. Navigates to the correct group (`condition/torque_level/channel`)
4. Retrieves the object reference for the requested repetition
5. Dereferences it to pull the actual array from the file's internal `#refs#` storage pool
6. Flattens the array from MATLAB's native `(N, 1)` column shape into a standard 1D array

**Important design decision — no hardcoded sample rates:** early versions hardcoded the vibration sample rate at 8,327 Hz, sourced from an unverified online estimate. This was found to be wrong when checked against real data — the true rate is 8,528.00 Hz, derived directly from `sample_count / 18` (the known recording duration). The final version of this script never hardcodes a rate; every caller derives it fresh from the actual array length it receives.

**Verified against:** both the healthy condition (`rs`) and at least one fault condition (`r1b`), confirming the extraction logic generalizes correctly across the dataset rather than being a one-off fit to a single file.

---

### 3.2 `simulator/sensor_simulator.py` — Virtual Edge Node

**Purpose:** Act as a stand-in for physical hardware (ESP32 + sensors) that has not yet arrived, by publishing real dataset signals over MQTT exactly as a genuine sensor node would.

**Why it exists:** This is the core piece of the project's hardware/software decoupling strategy. Rather than waiting for physical sensors, this script replays real, previously recorded motor data — but does so live, at realistic pacing, indistinguishable in structure and timing from an actual device. When real hardware arrives, it can be plugged into the same MQTT topic/schema contract with zero changes downstream.

**How it works:**
1. Imports `load_signal` directly from `loader.py` (via `sys.path` manipulation, since the two live in sibling folders)
2. Loads all 3 current channels (`Ia`, `Ib`, `Ic`) and all 5 vibration channels for the requested condition/torque combination
3. Derives the true sample rate for each signal type directly from the loaded array length (same principle as `loader.py` — never hardcoded)
4. Splits the full 18-second recording into fixed-duration windows (default: 1 second each), using `slice_window()` to compute the correct start/end sample indices per window
5. For each window, builds a JSON payload and publishes it to MQTT via `paho-mqtt`
6. Sleeps between windows (`time.sleep(window_duration_s / speed)`) to simulate real-time pacing — this is what makes it behave like a live stream rather than a fast file dump

**MQTT topic pattern:**
```
smartwatch/{factory_id}/{line_id}/{machine_id}/{sensor_group}
```
Example: `smartwatch/factory1/line1/motorA/current`

**JSON payload shape (current):**
```json
{
  "device_id": "sim-motor-01",
  "timestamp": "2026-08-01T16:03:55.554132+00:00",
  "sample_rate_hz": 55611.11,
  "window_duration_ms": 1000,
  "channels": {
    "Ia": [ ...raw samples... ],
    "Ib": [ ...raw samples... ],
    "Ic": [ ...raw samples... ]
  },
  "health_condition_sim": "rs",
  "torque_level_sim": "torque05"
}
```
Vibration payloads follow the same shape, with `Vib_axial`, `Vib_base`, `Vib_carc`, `Vib_acpe`, `Vib_acpi` as channel keys instead.

**Key design choices, and why:**
- **`timestamp` is generated fresh at publish time** (`datetime.now(timezone.utc)`), never reused from the dataset — this is what makes the data feel genuinely "live" rather than a historical replay.
- **`health_condition_sim` / `torque_level_sim` are simulator-only debug fields** — a real physical sensor would never know or send this; they exist purely so the pipeline has ground-truth fault labels available for later ML validation.
- Command-line configurable (`argparse`): health condition, torque level, device/factory/line/machine IDs, window duration, playback speed — allowing different fault scenarios to be simulated without code changes.

**Library used:** `paho-mqtt` (synchronous MQTT client) — chosen for the simulator specifically because it runs as a simple, sequential publish loop; no need for async here since it's not juggling concurrent I/O the way the consumer is.

**Verified:** publishes 18 windows per full run (matching the 18-second recording ÷ default 1-second window duration), confirmed received correctly by both a raw `mosquitto_sub` subscriber and later by `consumer.py`.

---

### 3.3 `consumer/consumer.py` — Ingestion Service

**Purpose:** Subscribe to the MQTT topics the simulator (and later, real hardware) publishes to, validate incoming data, and write it durably into TimescaleDB.

**Why it's async:** Uses `aiomqtt` (async MQTT client) and `asyncpg` (async Postgres driver) rather than synchronous equivalents. This matters because a blocking database write on a synchronous driver would stall the entire message-receiving loop — under any real load, incoming MQTT messages could be dropped while a slow database write is in progress. The async design lets the consumer keep listening while writes are in flight.

**How it works:**
1. Establishes an `asyncpg` connection pool to TimescaleDB at startup
2. Connects to the MQTT broker and subscribes using **wildcard topics**:
   ```
   smartwatch/+/+/+/current
   smartwatch/+/+/+/vibration
   ```
   The `+` wildcards mean this consumer works for *any* factory/line/machine combination without needing to know them in advance.
3. For every incoming message:
   - Parses the JSON payload
   - Extracts `machine_id` directly from the **topic path** (not from the payload body) — since the topic itself already encodes machine identity
   - Validates that all required fields and expected channel keys are present; if not, logs a rejection and moves on, rather than crashing or inserting incomplete data
   - Routes the payload to the correct insert function based on whether the topic ends in `/current` or `/vibration`
4. Inserts the validated row via a single parameterized SQL `INSERT`, storing the entire window's raw sample arrays directly as Postgres array columns

**Verified end-to-end:** with the simulator publishing 18 current + 18 vibration windows, the consumer wrote exactly 18 + 18 rows into TimescaleDB — a perfect, lossless match, confirmed via both live console output and direct SQL row counts.

---

### 3.4 `api/` — Backend API (FastAPI)

This is split into four files by responsibility, rather than one large script:

#### `api/config.py` — Configuration
Centralizes environment-dependent values: the database connection string (`DB_DSN`), JWT secret, algorithm, and token expiry. Uses `os.environ.get(..., default)` so real deployments can override these via environment variables without touching code, while local development falls back to sensible defaults.

#### `api/db.py` — Database Connection Management
Manages a single shared `asyncpg` connection pool for the whole API process — created once at startup (`connect()`), reused across every request, and cleanly closed at shutdown (`disconnect()`). This avoids the overhead and inefficiency of opening a new database connection per request.

#### `api/auth.py` — Authentication
Implements JWT-based authentication using `PyJWT`, backed by a real `users` table (see 3.4.1 below):
- `create_access_token(username, role)`: issues a signed token with a 60-minute expiry, carrying both the username and role in the payload
- `authenticate_user(username, password)`: now `async`, queries `users` by username and verifies the password with `passlib`'s bcrypt backend (`pwd_context.verify`) rather than comparing plaintext strings. When the username doesn't exist, a dummy hash comparison is still run so failed lookups take roughly the same time as failed password checks, avoiding a timing side-channel that could leak which usernames are valid
- `get_current_user(token)`: a FastAPI dependency that decodes and validates the JWT on every protected request, rejecting expired or malformed tokens with a 401; now returns a `{username, role}` dict rather than a bare string
- `require_admin(user)`: an additional dependency for routes that should be admin-only (not yet applied to any route, but available for future use)

**Password hashing note:** the project uses `passlib[bcrypt]`, which required pinning `bcrypt==4.0.1` specifically — newer `bcrypt` releases (4.1+) removed an internal attribute (`__about__.__version__`) that `passlib`'s version-detection code depends on, causing hashing to fail outright. This is a known, unresolved compatibility issue in the unmaintained `passlib` project.

#### 3.4.1 `users` table and account management scripts
The hardcoded test-user placeholder was replaced with a real Postgres table:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```
`role` defaults to `'viewer'` rather than `'admin'`, so every account must be explicitly promoted — the safer default. Two standalone scripts manage accounts directly against the database, since there is deliberately no public `/register` API route:
- `api/create_user.py <username> <password> [role]` — hashes the password with bcrypt and inserts a new row
- `api/reset_password.py <username> <new_password>` — updates an existing user's password hash in place, without needing to delete and recreate the account

**Note on the JWT signing key:** `config.py` now prints a visible warning at startup if `JWT_SECRET` is left at its insecure default, so it isn't silently forgotten before a demo. `PyJWT` also emits an `InsecureKeyLengthWarning` if the configured secret is shorter than 32 bytes (HMAC-SHA256's recommended minimum) — harmless for local development, but worth using a longer secret to silence it.

#### `api/main.py` — Route Definitions
The actual FastAPI application and its endpoints:

| Endpoint | Method | Auth required | Purpose |
|---|---|---|---|
| `/health` | GET | No | Basic liveness check |
| `/auth/login` | POST | No | Exchanges username/password for a JWT |
| `/machines` | GET | Yes | Lists distinct machine IDs seen in telemetry, with last-seen time and window count |
| `/telemetry/current` | GET | Yes | Time-range and machine-filtered query over `telemetry_current` |
| `/telemetry/vibration` | GET | Yes | Same, over `telemetry_vibration` |

**Design note on `/machines`:** rather than requiring a separate `machines` registry table to exist before this endpoint could work, it derives its machine list directly from `SELECT DISTINCT machine_id ... FROM telemetry_current UNION telemetry_vibration` — meaning it reflects real, live data from day one. A proper `machines` metadata table (with fields like installation date, motor specs, etc.) can be added later without breaking this endpoint's existing contract.

**Design note on telemetry queries:** built with dynamically constructed `WHERE` clauses (`build_telemetry_query()`) so that `machine_id`, `start`, and `end` filters are all optional and combinable, using parameterized queries throughout (`$1`, `$2`, ...) to prevent SQL injection. `limit` is also now server-side capped (`MAX_TELEMETRY_LIMIT = 1000`, via `min(max(q.limit, 1), MAX_TELEMETRY_LIMIT)`), so a client passing an excessively large or negative/zero value can't force an unbounded query.

**CORS:** `CORSMiddleware` is registered on the app so a future browser-based dashboard (running on a different origin, e.g. a Vite dev server) can call the API without being blocked by same-origin restrictions. Currently configured wide-open (`allow_origins=["*"]`) for local development, explicitly marked as temporary — this should be scoped to the dashboard's real origin before anything resembling a production deployment.

**Verified end-to-end:** after populating TimescaleDB via the simulator + consumer, `GET /auth/login`, `GET /machines`, and `GET /telemetry/current` were all confirmed to return real, live data through the actual HTTP API (not just via direct database queries) — proving the entire chain works from raw sensor recording through to an authenticated REST response.

---

## 4. Technologies, Applications, and Services Used

### 4.1 Languages
- **Python** — used for every backend component (loader, simulator, consumer, API)

### 4.2 Core Python Libraries

| Library | Used in | Purpose |
|---|---|---|
| `h5py` | `loader.py` | Reads HDF5-format files (MATLAB v7.3 `.mat` files) |
| `numpy` | `loader.py`, `sensor_simulator.py` | Array manipulation, flattening, slicing |
| `paho-mqtt` | `sensor_simulator.py` | Synchronous MQTT publishing client |
| `aiomqtt` | `consumer.py` | Asynchronous MQTT subscriber client |
| `asyncpg` | `consumer.py`, `api/db.py` | Asynchronous PostgreSQL driver |
| `FastAPI` | `api/main.py` | Web framework for the REST API |
| `uvicorn` | `api/` (runtime) | ASGI server that actually runs the FastAPI app |
| `PyJWT` | `api/auth.py` | JSON Web Token creation and verification |
| `pydantic` | `api/main.py` | Request/response data validation (used via FastAPI) |
| `python-multipart` | `api/` (runtime) | Required by FastAPI to parse OAuth2 login form data |

### 4.3 Infrastructure / Services

| Technology | Role | Notes |
|---|---|---|
| **Eclipse Mosquitto** | MQTT message broker | Run in Docker; all telemetry passes through this before reaching the consumer |
| **TimescaleDB** (PostgreSQL + extension) | Time-series database | Run in Docker; stores telemetry as hypertables, partitioned automatically by time |
| **Docker / Docker Desktop** | Containerization | Runs Mosquitto and TimescaleDB in isolated, reproducible containers |
| **Docker named volumes** | Persistent storage | Ensures TimescaleDB's data survives container restarts (added after an early incident where a volume-less container lost its data) |

`requirements.txt` (at `Backend/`) pins dependency versions across all four components (API, consumer, simulator, loader) for reproducibility — including the `bcrypt==4.0.1` pin required by the `passlib` compatibility issue noted in 3.4. `docker-compose.yml` and `mosquitto/config/mosquitto.conf` codify the TimescaleDB and Mosquitto container setup that was previously only run via ad hoc `docker run` commands.

### 4.4 Dataset

**UNIOESTE/USP Broken Rotor Bar Dataset** (Treml et al., published via IEEE DataPort) — a real induction motor rig recording (1hp, 4-pole, 60Hz), used as the "hardware substitute" throughout software development. Provides 5 health conditions, 8 torque levels, 10 repetitions each, with synchronized 3-phase current, 3-phase voltage, a trigger signal, and 5-channel vibration data.

### 4.5 Development Tools
- **VS Code** — primary editor
- **PowerShell** — command-line environment (Windows)
- **psql** — PostgreSQL's command-line client, used for direct database inspection and manual schema creation
- **Swagger UI** (auto-generated by FastAPI at `/docs`) — used for manually testing every API endpoint, including the full JWT login → authorize → query flow

---

## 5. Known Issues Resolved (Worth Remembering)

### 5.1 Incorrect secondhand sample rate
An unverified online estimate for the vibration channel sample rate (8,327 Hz) was found to be wrong once checked against real extracted data. The true rate — 8,528.00 Hz — was derived directly from `sample_count / 18s`. Fixed by making `loader.py` always compute sample rate from real data, never from a hardcoded constant.

### 5.2 OneDrive silently delaying file access
The dataset lived under a OneDrive-synced folder with Files On-Demand enabled, causing large files to be cloud-only placeholders. First access silently triggered a slow background download, initially appearing as a hung script. Fixed by marking the dataset folder "Always keep on this device."

### 5.3 TimescaleDB container losing data after a restart
The original `docker run` command for TimescaleDB had no persistent volume, meaning all data lived inside the container's writable layer. After the container restarted, previously created tables appeared to be gone (though in this specific case, later investigation revealed the tables actually survived — the deeper issue turned out to be 5.2 below). A named volume (`-v timescale_data:/var/lib/postgresql/data`) was added regardless, as a correctness fix independent of what actually caused the visible symptom.

### 5.4 Port 5432 conflict with a native PostgreSQL installation
The most significant bug encountered: a native PostgreSQL 18 Windows service (`postgresql-x64-18`) was already listening on port 5432, entirely independent of Docker. Docker's TimescaleDB container was *also* mapped to port 5432. As a result, every connection from Windows-side Python code (`asyncpg`, and therefore both `consumer.py` and the FastAPI app) was silently routed to the empty native Postgres instance instead of the Docker container — while direct `docker exec ... psql` connections (which bypass the host network entirely) correctly saw the container's real tables. This produced a confusing situation where the same tables appeared to both exist and not exist, depending on which tool was used to check.

**Diagnosis method:** `netstat -ano | findstr :5432` revealed two separate processes bound to the same port; `tasklist` identified them as `postgres.exe` (native service) and `com.docker.backend.exe` (Docker).

**Fix:** recreated the TimescaleDB container on a non-conflicting host port (`-p 5433:5432`), and updated `DB_DSN` in every consuming script (`api/config.py`, `consumer/consumer.py`) to point at `localhost:5433` instead of the default `5432`.

### 5.5 Duplicate route definitions silently shadowing real endpoints
While updating `main.py`'s route signatures to match `auth.py`'s new dict-returning `get_current_user`, only a signature-only edit was intended, but the edit was applied by adding new stub function bodies (`...`) above the existing, fully-implemented routes rather than editing them in place. FastAPI/Starlette matches routes in registration order, so the first definition of a path wins — meaning `/machines`, `/telemetry/current`, and `/telemetry/vibration` all silently returned `null` (the stub bodies' implicit return value) while the real implementations lower in the file were never reached. No error was raised; the bug only became visible because the endpoints returned empty/null data instead of real telemetry. Fixed by removing the stub duplicates and updating only the type hints (`user: str` → `user: dict`) on the original route functions.

**Lesson:** a duplicate route definition in FastAPI fails silently — no startup warning, no runtime error — so it's worth explicitly diffing route counts (`grep -c "@app.get\|@app.post"`) after any edit that touches route decorators.

### 5.6 `passlib` / `bcrypt` version incompatibility
Installing `passlib[bcrypt]` alongside a recent `bcrypt` (5.x) release caused password hashing to fail with `AttributeError: module 'bcrypt' has no attribute '__about__'`, followed by a `ValueError` about a 72-byte password limit — a red herring masking the real cause. `passlib` (last released 2020, effectively unmaintained) does version detection by reading `bcrypt.__about__.__version__`, an attribute removed in `bcrypt` 4.1+. **Fix:** pinned `bcrypt==4.0.1` explicitly in `requirements.txt`, the last version compatible with `passlib`'s detection code.

---

## 6. Current Verified State

As of this document, the following has been independently confirmed to work with real (not placeholder) data, end-to-end:

1. ✅ `loader.py` correctly extracts real signals from the dataset, verified visually (waveform matches known motor-startup physics) and numerically (sample rates match derived, non-guessed values)
2. ✅ `sensor_simulator.py` publishes real dataset windows over MQTT at realistic pacing with live timestamps
3. ✅ `consumer.py` receives every published window and writes it losslessly into TimescaleDB (18 windows in → 18 rows out, for both current and vibration)
4. ✅ `main.py` (FastAPI) successfully authenticates via JWT and returns real, live telemetry data through `GET /machines` and `GET /telemetry/current`, reading from the same database the consumer wrote into
5. ✅ Auth is now backed by a real `users` table with bcrypt-hashed passwords (no more hardcoded test credentials), with `create_user.py` / `reset_password.py` for account management
6. ✅ Duplicate/shadowed route definitions in `main.py` (see 5.5) identified and removed — confirmed via a fresh end-to-end run (login → `/machines` → `/telemetry/current`) that all three protected endpoints return real data, not `null`
7. ✅ CORS middleware and server-side `limit` capping added to `main.py`, ahead of dashboard integration

**Phase 3 (backend hardening) is now considered complete.** Next planned phase: Phase 4, Hardware-in-the-Loop simulation — exercising the pipeline against additional fault conditions (`r1b`–`r4b`, broken rotor bars) beyond the healthy (`rs`) baseline used during initial verification.

This represents a fully functioning pipeline from raw industrial sensor data through to an authenticated, queryable REST API — the complete backbone the eventual ML pipeline (Phase 4) and dashboard (Phase 5) will build on top of.
