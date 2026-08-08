import h5py
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(r'C:\Users\ibrah\OneDrive\Desktop\Btech-Major')
DATASET_DIR = PROJECT_ROOT / '5.Dataset' / 'Experimental Database'

RECORDING_DURATION_SECONDS = 18  # confirmed from dataset documentation

CURRENT_VOLTAGE_CHANNELS = {'Ia', 'Ib', 'Ic', 'Va', 'Vb', 'Vc', 'Trigger'}
VIBRATION_CHANNELS = {'Vib_axial', 'Vib_base', 'Vib_carc', 'Vib_acpe', 'Vib_acpi'}


def load_signal(health_condition: str, torque_level: str, channel: str,
                 repetition: int = 0, file_suffix: str = 'R1') -> np.ndarray:
    """
    Load one signal channel from the broken rotor bar dataset.

    Parameters
    ----------
    health_condition : str
        'rs' (healthy), 'r1b', 'r2b', 'r3b', 'r4b' (1-4 broken bars)
    torque_level : str
        'torque05' through 'torque40' (0.5 Nm to 4.0 Nm, step 0.5)
    channel : str
        e.g. 'Ia', 'Ib', 'Ic', 'Va', 'Vb', 'Vc', 'Trigger',
        'Vib_axial', 'Vib_base', 'Vib_carc', 'Vib_acpe', 'Vib_acpi'
    repetition : int
        Index 0-9 (10 repetitions available per condition)
    file_suffix : str
        Matches the dataset filename pattern, e.g. struct_rs_R1.mat

    Returns
    -------
    np.ndarray
        1D array of the signal values
    """
    filename = f"struct_{health_condition}_{file_suffix}.mat"
    file_path = DATASET_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    with h5py.File(file_path, 'r') as f:
        group = f[health_condition][torque_level]
        if channel not in group:
            raise KeyError(f"Channel '{channel}' not found. Available: {list(group.keys())}")

        ref = group[channel][repetition, 0]
        data = f[ref][:]

    return data.flatten()


def get_sample_rate(num_samples: int) -> float:
    """
    Derive the actual sample rate from sample count and known recording duration.
    Do NOT hardcode sample rates — different channels/files may vary slightly.
    Always compute this from the real loaded array.
    """
    return num_samples / RECORDING_DURATION_SECONDS


def get_time_axis(num_samples: int) -> np.ndarray:
    """Build a time axis in seconds, derived from the actual sample count."""
    fs = get_sample_rate(num_samples)
    return np.arange(num_samples) / fs


def channel_category(channel: str) -> str:
    """Return 'current_voltage' or 'vibration' for reference/logging purposes."""
    if channel in CURRENT_VOLTAGE_CHANNELS:
        return 'current_voltage'
    elif channel in VIBRATION_CHANNELS:
        return 'vibration'
    else:
        raise ValueError(f"Unknown channel: {channel}")


# Test
if __name__ == "__main__":
    test_channels = ['Ia', 'Vib_axial', 'Vib_base', 'Ic']

    for ch in test_channels:
        signal = load_signal(health_condition='rs', torque_level='torque05', channel=ch, repetition=0)
        fs = get_sample_rate(signal.shape[0])
        print(f"{ch:12s} | category={channel_category(ch):15s} | "
              f"samples={signal.shape[0]:>8} | derived sample rate={fs:.2f} Hz")