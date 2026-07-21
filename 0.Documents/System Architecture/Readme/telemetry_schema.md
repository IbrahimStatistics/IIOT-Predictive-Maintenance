# SmartWatch Manager — Telemetry Schema

## Topic Structure
Sparkplug-style hierarchy, one topic per sensor group:

smartwatch/{factory_id}/{line_id}/{machine_id}/current
smartwatch/{factory_id}/{line_id}/{machine_id}/vibration

Example: `smartwatch/factory1/line1/motorA/current`

## Design Rationale
- Current (Ia/Ib/Ic) and vibration (5 channels) are separated into distinct topics
  because they have different native sample rates and serve different fault-detection
  purposes (MCSA vs. mechanical vibration analysis).
- Channels within each group are published together in one payload, not as separate
  messages, because they must remain time-synchronized for FFT/MCSA feature extraction
  — this also mirrors how real firmware would batch a shared ADC read.
- `timestamp` is always generated at publish time, never taken from source data files.
  This is what allows the telemetry simulator to produce a stream indistinguishable
  from live hardware.

## Current Payload
```json
{
  "device_id": "sim-motor-01",
  "timestamp": "2026-07-21T14:32:05.123Z",
  "sample_rate_hz": 55611.11,
  "window_duration_ms": 1000,
  "channels": {
    "Ia": [...],
    "Ib": [...],
    "Ic": [...]
  },
  "health_condition_sim": "rs",
  "torque_level_sim": "torque05"
}
```

## Vibration Payload
```json
{
  "device_id": "sim-motor-01",
  "timestamp": "2026-07-21T14:32:05.123Z",
  "sample_rate_hz": 8528.0,
  "window_duration_ms": 1000,
  "channels": {
    "Vib_axial": [...],
    "Vib_base": [...],
    "Vib_carc": [...],
    "Vib_acpe": [...],
    "Vib_acpi": [...]
  },
  "health_condition_sim": "rs",
  "torque_level_sim": "torque05"
}
```

## Field Reference
| Field | Type | Notes |
|---|---|---|
| `device_id` | string | Distinguishes simulator (`sim-*`) from real hardware (`esp32-*`) on the same topic contract |
| `timestamp` | ISO 8601 UTC | Publish-time generated, not from source data |
| `sample_rate_hz` | float | Derived dynamically from source data, never hardcoded |
| `window_duration_ms` | int | Duration of the batched window, currently 1000ms |
| `channels` | object | Channel name → array of raw sample values |
| `health_condition_sim` | string | **Simulator-only.** Ground-truth label from source dataset. Real hardware cannot produce this — must be stripped or ignored by any consumer logic that expects to work with real hardware later |
| `torque_level_sim` | string | **Simulator-only.** Same caveat as above |

## Known Limitations / Future Revisions
- Window duration (1000ms) is a starting default, not yet benchmarked against payload
  size or broker performance — revisit once simulator is running end-to-end.
- `health_condition_sim` / `torque_level_sim` are a deliberate temporary scope
  expansion for development convenience — removal is a tracked follow-up before
  this schema is considered "final" for hardware integration.