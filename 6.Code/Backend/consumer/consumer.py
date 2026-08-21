"""
    consumer.py

    Async MQTT -> TimescaleDB ingestion pipeline.

    Subscribes to a wildcard MQTT topic, parses machine_id and sensor_type from
    the topic path, and writes one row per window into the appropriate
    hypertable (telemetry_current or telemetry_vibration) with raw samples
    stored as DOUBLE PRECISION[] columns.

    Assumed topic schema (adjust TOPIC_FILTER / parsing if yours differs):
        iiot/<machine_id>/current
        iiot/<machine_id>/vibration

    Assumed JSON payload schema (matches sensor_simulator.py output):
    {
        "machine_id": "motorA",
        "timestamp": "2026-08-14T10:32:01.123456Z",
        "sample_rate_hz": 55611.0,
        "channels": {
            "Ia": [0.123, 0.456, ...],
            "Ib": [...],
            "Ic": [...]
        }
    }
    """

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import aiomqtt
import asyncpg

# consumer.py lives in consumer/, config.py lives in a sibling api/ folder —
# add api/ to the import path so `from config import DB_DSN` resolves.
sys.path.append(str(Path(__file__).resolve().parent.parent / "api"))

from config import DB_DSN
# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MQTT_HOST = "localhost"
MQTT_PORT = 1883
TOPIC_FILTER = "smartwatch/+/+/+/+"  # smartwatch/<factory>/<line>/<machine>/<sensor_type>

# Map sensor_type (from topic) -> (table_name, expected channel keys)
TABLE_MAP = {
    "current": ("telemetry_current", ["Ia", "Ib", "Ic"]),
    "vibration": ("telemetry_vibration", ["Vib_axial", "Vib_base", "Vib_carc", "Vib_acpe", "Vib_acpi"]),
}

RECONNECT_DELAY_SECONDS = 5
DB_POOL_MIN_SIZE = 2
DB_POOL_MAX_SIZE = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("consumer")


# ---------------------------------------------------------------------------
# DB layer
# ---------------------------------------------------------------------------

async def create_pool() -> asyncpg.Pool:
    pool = await asyncpg.create_pool(
        dsn=DB_DSN,
        min_size=DB_POOL_MIN_SIZE,
        max_size=DB_POOL_MAX_SIZE,
    )
    logger.info("Connected to TimescaleDB (pool size %d-%d)", DB_POOL_MIN_SIZE, DB_POOL_MAX_SIZE)
    return pool


async def insert_window(pool: asyncpg.Pool, table: str, channel_cols: list[str], row: dict) -> None:
    columns = ["machine_id", "time", "sample_rate_hz"] + channel_cols
    placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
    col_list = ", ".join(f'"{c}"' for c in columns)  # ← quote every identifier

    values = [row["machine_id"], row["ts"], row["sample_rate_hz"]]
    values.extend(row["channels"][c] for c in channel_cols)

    query = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"

    async with pool.acquire() as conn:
        await conn.execute(query, *values)

# ---------------------------------------------------------------------------
# Payload parsing / validation
# ---------------------------------------------------------------------------

def parse_topic(topic: str) -> tuple[str, str] | None:
    """smartwatch/<factory>/<line>/<machine>/<sensor_type> -> (machine_id, sensor_type)"""
    parts = topic.split("/")
    if len(parts) != 5 or parts[0] != "smartwatch":
        return None
    machine_id = parts[3]
    sensor_type = parts[4]
    return machine_id, sensor_type


def parse_payload(raw_payload: bytes, expected_channels: list[str]) -> dict | None:
    try:
        data = json.loads(raw_payload)
    except json.JSONDecodeError:
        logger.warning("Dropping message: invalid JSON")
        return None

    required_keys = {"timestamp", "sample_rate_hz", "channels"}
    if not required_keys.issubset(data):
        logger.warning("Dropping message: missing keys %s", required_keys - set(data))
        return None

    channels = data["channels"]
    if not all(ch in channels for ch in expected_channels):
        logger.warning(
            "Dropping message: expected channels %s, got %s",
            expected_channels, list(channels.keys()),
        )
        return None

    try:
        ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Dropping message: unparseable timestamp %r", data["timestamp"])
        return None

    return {
        "ts": ts,
        "sample_rate_hz": float(data["sample_rate_hz"]),
        "channels": channels,
    }


# ---------------------------------------------------------------------------
# Main consume loop
# ---------------------------------------------------------------------------

async def handle_message(pool: asyncpg.Pool, topic: str, raw_payload: bytes) -> None:
    parsed_topic = parse_topic(topic)
    if parsed_topic is None:
        logger.warning("Dropping message: unrecognized topic %r", topic)
        return

    machine_id, sensor_type = parsed_topic

    table_entry = TABLE_MAP.get(sensor_type)
    if table_entry is None:
        logger.warning("Dropping message: unknown sensor_type %r on topic %r", sensor_type, topic)
        return

    table, channel_cols = table_entry

    row = parse_payload(raw_payload, channel_cols)
    if row is None:
        return
    row["machine_id"] = machine_id

    if row["machine_id"] != machine_id:
        logger.warning(
            "Topic/payload machine_id mismatch (topic=%s, payload=%s); using topic value",
            machine_id, row["machine_id"],
        )
        row["machine_id"] = machine_id

    try:
        await insert_window(pool, table, channel_cols, row)
        logger.info(
            "Inserted window: machine=%s table=%s ts=%s",
            machine_id, table, row["ts"].isoformat(),
        )
    except asyncpg.PostgresError:
        logger.exception("DB insert failed for machine=%s table=%s", machine_id, table)


async def consume_forever(pool: asyncpg.Pool) -> None:
    while True:
        try:
            async with aiomqtt.Client(hostname=MQTT_HOST, port=MQTT_PORT) as client:
                await client.subscribe(TOPIC_FILTER)
                logger.info("Subscribed to %s on %s:%d", TOPIC_FILTER, MQTT_HOST, MQTT_PORT)

                async for message in client.messages:
                    topic = str(message.topic)
                    payload = message.payload
                    if isinstance(payload, (bytearray, memoryview)):
                        payload = bytes(payload)
                    # Fire-and-forget per message so a slow insert doesn't
                    # block the MQTT receive loop. Swap to `await` directly
                    # if you need strict in-order processing.
                    asyncio.create_task(handle_message(pool, topic, payload))

        except aiomqtt.MqttError as e:
            logger.error("MQTT connection lost (%s); reconnecting in %ds", e, RECONNECT_DELAY_SECONDS)
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)


async def main() -> None:
    pool = await create_pool()
    try:
        await consume_forever(pool)
    finally:
        await pool.close()


if __name__ == "__main__":
    # On Windows, the default ProactorEventLoop doesn't implement
    # add_reader/add_writer, which aiomqtt (via paho-mqtt) needs.
    # loop_factory (Python 3.12+) forces the selector loop directly,
    # since the older set_event_loop_policy() approach is no longer
    # reliably honored on recent Python versions (e.g. 3.14).
    if sys.platform == "win32":
        asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(main())