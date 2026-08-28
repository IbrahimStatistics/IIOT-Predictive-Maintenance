-- SmartWatch Manager — TimescaleDB schema
-- Column names match consumer.py's insert_window() and main.py's queries.

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ---------------------------------------------------------------------
-- Current (electrical) telemetry — channels Ia, Ib, Ic
-- ---------------------------------------------------------------------
CREATE TABLE telemetry_current (
    machine_id      TEXT NOT NULL,
    time            TIMESTAMPTZ NOT NULL,
    sample_rate_hz  DOUBLE PRECISION,
    "Ia"            DOUBLE PRECISION[] NOT NULL,
    "Ib"            DOUBLE PRECISION[] NOT NULL,
    "Ic"            DOUBLE PRECISION[] NOT NULL,
    PRIMARY KEY (machine_id, time)
);
SELECT create_hypertable('telemetry_current', 'time');

-- ---------------------------------------------------------------------
-- Vibration telemetry — 5 MAFAULDA accelerometer channels
-- (confirmed via \d telemetry_vibration — NOT the 3-axis Ax/Ay/Az
-- originally assumed; that mismatch caused a live 500 error, fixed here)
-- ---------------------------------------------------------------------
CREATE TABLE telemetry_vibration (
    machine_id      TEXT NOT NULL,
    time            TIMESTAMPTZ NOT NULL,
    sample_rate_hz  DOUBLE PRECISION,
    "Vib_axial"     DOUBLE PRECISION[] NOT NULL,
    "Vib_base"      DOUBLE PRECISION[] NOT NULL,
    "Vib_carc"      DOUBLE PRECISION[] NOT NULL,
    "Vib_acpe"      DOUBLE PRECISION[] NOT NULL,
    "Vib_acpi"      DOUBLE PRECISION[] NOT NULL,
    PRIMARY KEY (machine_id, time)
);
SELECT create_hypertable('telemetry_vibration', 'time');

-- ---------------------------------------------------------------------
-- Auth — matches auth.py / create_user.py / reset_password.py
-- Merged from migrations/001_create_users.sql: id as PK (better for
-- future FKs), username UNIQUE, created_at for auditing.
-- role default is 'viewer' (least-privilege) — create_user.py always
-- passes role explicitly, so this only matters as a fallback.
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id                SERIAL PRIMARY KEY,
    username          VARCHAR(50) UNIQUE NOT NULL,
    hashed_password   VARCHAR(255) NOT NULL,
    role              VARCHAR(20) NOT NULL DEFAULT 'viewer',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);