import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import paho.mqtt.client as mqtt

sys.path.append(str(Path(__file__).resolve().parent.parent / "loader"))
from loader import load_signal

RECORDING_DURATION_SECONDS = 18
CURRENT_CHANNELS = ["Ia", "Ib", "Ic"]
VIBRATION_CHANNELS = ["Vib_axial", "Vib_base", "Vib_carc", "Vib_acpe", "Vib_acpi"]

MQTT_BROKER = "localhost"
MQTT_PORT = 1883


def build_topic(factory_id, line_id, machine_id, sensor_group):
    return f"smartwatch/{factory_id}/{line_id}/{machine_id}/{sensor_group}"


def slice_window(signal: np.ndarray, sample_rate: float, window_index: int, window_duration_s: float):
    start = int(window_index * window_duration_s * sample_rate)
    end = int((window_index + 1) * window_duration_s * sample_rate)
    return signal[start:end]


def run_simulator(health_condition, torque_level, device_id,
                   factory_id, line_id, machine_id,
                   window_duration_s=1.0, speed=1.0):

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER, MQTT_PORT)

    current_signals = {
        ch: load_signal(health_condition, torque_level, ch) for ch in CURRENT_CHANNELS
    }
    vibration_signals = {
        ch: load_signal(health_condition, torque_level, ch) for ch in VIBRATION_CHANNELS
    }

    fs_current = current_signals["Ia"].shape[0] / RECORDING_DURATION_SECONDS
    fs_vibration = vibration_signals["Vib_axial"].shape[0] / RECORDING_DURATION_SECONDS

    num_windows = int(RECORDING_DURATION_SECONDS / window_duration_s)

    print(f"Starting simulation: {device_id} | {health_condition} | {torque_level}")
    print(f"Current fs={fs_current:.2f}Hz | Vibration fs={fs_vibration:.2f}Hz | {num_windows} windows")

    for w in range(num_windows):
        timestamp = datetime.now(timezone.utc).isoformat()

        current_payload = {
            "device_id": device_id,
            "timestamp": timestamp,
            "sample_rate_hz": round(fs_current, 2),
            "window_duration_ms": int(window_duration_s * 1000),
            "channels": {
                ch: slice_window(sig, fs_current, w, window_duration_s).tolist()
                for ch, sig in current_signals.items()
            },
            "health_condition_sim": health_condition,
            "torque_level_sim": torque_level,
        }
        client.publish(build_topic(factory_id, line_id, machine_id, "current"), json.dumps(current_payload))

        vibration_payload = {
            "device_id": device_id,
            "timestamp": timestamp,
            "sample_rate_hz": round(fs_vibration, 2),
            "window_duration_ms": int(window_duration_s * 1000),
            "channels": {
                ch: slice_window(sig, fs_vibration, w, window_duration_s).tolist()
                for ch, sig in vibration_signals.items()
            },
            "health_condition_sim": health_condition,
            "torque_level_sim": torque_level,
        }
        client.publish(build_topic(factory_id, line_id, machine_id, "vibration"), json.dumps(vibration_payload))

        print(f"  Window {w+1}/{num_windows} published at {timestamp}")
        time.sleep(window_duration_s / speed)

    client.disconnect()
    print("Simulation complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SmartWatch telemetry simulator")
    parser.add_argument("--health", default="rs")
    parser.add_argument("--torque", default="torque05")
    parser.add_argument("--device-id", default="sim-motor-01")
    parser.add_argument("--factory", default="factory1")
    parser.add_argument("--line", default="line1")
    parser.add_argument("--machine", default="motorA")
    parser.add_argument("--window-ms", type=float, default=1000)
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()

    run_simulator(
        health_condition=args.health,
        torque_level=args.torque,
        device_id=args.device_id,
        factory_id=args.factory,
        line_id=args.line,
        machine_id=args.machine,
        window_duration_s=args.window_ms / 1000,
        speed=args.speed,
    )