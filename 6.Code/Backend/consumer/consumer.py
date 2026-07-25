import asyncio
import sys
import json
from datetime import datetime

# Fix for aiomqtt on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import asyncpg
from aiomqtt import Client, MqttError

MQTT_HOST = "localhost"
MQTT_PORT = 1883

TOPIC_CURRENT = "smartwatch/+/+/+/current"
TOPIC_VIBRATION = "smartwatch/+/+/+/vibration"

DB_DSN = "postgresql://postgres:yourpassword@localhost:5432/postgres"

CURRENT_CHANNELS = ["Ia", "Ib", "Ic"]
VIBRATION_CHANNELS = [
    "Vib_axial",
    "Vib_base",
    "Vib_carc",
    "Vib_acpe",
    "Vib_acpi",
]


def parse_machine_id(topic: str) -> str:
    parts = topic.split("/")
    return parts[3]


def validate_payload(payload: dict, expected_channels: list[str]) -> bool:
    required = {"device_id", "timestamp", "sample_rate_hz", "channels"}
    missing = required - payload.keys()

    if missing:
        print(f"[REJECTED] Missing top-level fields: {missing}")
        return False

    missing_channels = set(expected_channels) - payload["channels"].keys()

    if missing_channels:
        print(f"[REJECTED] Missing channels: {missing_channels}")
        return False

    return True


async def insert_current(pool: asyncpg.Pool, machine_id: str, payload: dict):
    ch = payload["channels"]

    await pool.execute(
        """
        INSERT INTO telemetry_current
        (time, machine_id, health_condition, torque_level,
         sample_rate_hz, ia, ib, ic)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        """,
        datetime.fromisoformat(payload["timestamp"]),
        machine_id,
        payload.get("health_condition_sim"),
        payload.get("torque_level_sim"),
        payload["sample_rate_hz"],
        ch["Ia"],
        ch["Ib"],
        ch["Ic"],
    )


async def insert_vibration(pool: asyncpg.Pool, machine_id: str, payload: dict):
    ch = payload["channels"]

    await pool.execute(
        """
        INSERT INTO telemetry_vibration
        (time, machine_id, health_condition, torque_level,
         sample_rate_hz, vib_axial, vib_base,
         vib_carc, vib_acpe, vib_acpi)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        """,
        datetime.fromisoformat(payload["timestamp"]),
        machine_id,
        payload.get("health_condition_sim"),
        payload.get("torque_level_sim"),
        payload["sample_rate_hz"],
        ch["Vib_axial"],
        ch["Vib_base"],
        ch["Vib_carc"],
        ch["Vib_acpe"],
        ch["Vib_acpi"],
    )


async def main():
    pool = await asyncpg.create_pool(DB_DSN)
    print("Connected to TimescaleDB.")

    try:
        async with Client(hostname=MQTT_HOST, port=MQTT_PORT) as client:
            await client.subscribe(TOPIC_CURRENT)
            await client.subscribe(TOPIC_VIBRATION)

            print("Subscribed successfully.")

            async for message in client.messages:
                topic = str(message.topic)

                try:
                    payload = json.loads(message.payload)
                except json.JSONDecodeError:
                    print(f"[REJECTED] Malformed JSON on {topic}")
                    continue

                machine_id = parse_machine_id(topic)

                if topic.endswith("/current"):
                    if validate_payload(payload, CURRENT_CHANNELS):
                        await insert_current(pool, machine_id, payload)
                        print(
                            f"[OK] Current written | Machine={machine_id} | Device={payload['device_id']}"
                        )

                elif topic.endswith("/vibration"):
                    if validate_payload(payload, VIBRATION_CHANNELS):
                        await insert_vibration(pool, machine_id, payload)
                        print(
                            f"[OK] Vibration written | Machine={machine_id} | Device={payload['device_id']}"
                        )

    finally:
        await pool.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except MqttError as e:
        print(f"MQTT connection error: {e}")
    except KeyboardInterrupt:
        print("\nConsumer stopped.")