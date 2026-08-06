from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

import db
from auth import authenticate_user, create_access_token, get_current_user

app = FastAPI(title="SmartWatch Manager API")

# TEMPORARY: wide open for local dev. Tighten allow_origins to your actual
# dashboard URL before anything resembling a real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()


@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Auth ---

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(user["username"], user["role"])
    return {"access_token": token, "token_type": "bearer"}

# --- Machines ---

@app.get("/machines")
async def list_machines(user: dict = Depends(get_current_user)):
    pool = db.get_pool()
    rows = await pool.fetch(
        """
        SELECT machine_id,
               max(time) AS last_seen,
               count(*) AS window_count
        FROM (
            SELECT machine_id, time FROM telemetry_current
            UNION ALL
            SELECT machine_id, time FROM telemetry_vibration
        ) combined
        GROUP BY machine_id
        ORDER BY machine_id
        """
    )
    return [dict(r) for r in rows]


# --- Telemetry ---

MAX_TELEMETRY_LIMIT = 1000


class TelemetryQuery(BaseModel):
    machine_id: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    limit: int = 100


def build_telemetry_query(table: str, q: TelemetryQuery):
    conditions = []
    params = []
    idx = 1

    if q.machine_id:
        conditions.append(f"machine_id = ${idx}")
        params.append(q.machine_id)
        idx += 1
    if q.start:
        conditions.append(f"time >= ${idx}")
        params.append(q.start)
        idx += 1
    if q.end:
        conditions.append(f"time <= ${idx}")
        params.append(q.end)
        idx += 1

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    safe_limit = min(max(q.limit, 1), MAX_TELEMETRY_LIMIT)
    query = f"SELECT * FROM {table} {where_clause} ORDER BY time DESC LIMIT ${idx}"
    params.append(safe_limit)
    return query, params


@app.get("/telemetry/current")
async def get_current_telemetry(
    machine_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user),
):
    q = TelemetryQuery(machine_id=machine_id, start=start, end=end, limit=limit)
    query, params = build_telemetry_query("telemetry_current", q)
    pool = db.get_pool()
    rows = await pool.fetch(query, *params)
    return [dict(r) for r in rows]


@app.get("/telemetry/vibration")
async def get_vibration_telemetry(
    machine_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user),
):
    q = TelemetryQuery(machine_id=machine_id, start=start, end=end, limit=limit)
    query, params = build_telemetry_query("telemetry_vibration", q)
    pool = db.get_pool()
    rows = await pool.fetch(query, *params)
    return [dict(r) for r in rows]