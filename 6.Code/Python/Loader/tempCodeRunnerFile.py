import h5py
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(r'C:\Users\ibrah\OneDrive\Desktop\Btech-Major')
DATASET_DIR = PROJECT_ROOT / '5.Dataset' / 'Experimental Database'

# Sample rates confirmed directly from data (Phase 0)
SAMPLE_RATES = {
    'current': 55611,   # Ia, Ib, Ic, Va, Vb, Vc, Trigger
    'vibration': 8327,  # Vib_axial, Vib_base, Vib_carc, Vib_acpe, Vib_acpi
}

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


def get_sample_rate(channel: str) -> int:
    """Return the correct sample rate for a given channel name."""
    if channel in CURRENT_VOLTAGE_CHANNELS:
        return SAMPLE_RATES['current']
    elif channel in VIBRATION_CHANNELS:
        return SAMPLE_RATES['vibration']
    else:
        raise ValueError(f"Unknown channel: {channel}")


def get_time_axis(channel: str, num_samples: int) -> np.ndarray:
    """Build a time axis in seconds for a given channel and sample count."""
    fs = get_sample_rate(channel)
    return np.arange(num_samples) / fs


# Quick self-test when run directly
if __name__ == "__main__":
    signal = load_signal(health_condition='rs', torque_level='torque05', channel='Ia', repetition=0)
    print(f"Loaded Ia: {signal.shape[0]} samples, sample rate = {get_sample_rate('Ia')} Hz")

    vib_signal = load_signal(health_condition='rs', torque_level='torque05', channel='Vib_axial', repetition=0)
    print(f"Loaded Vib_axial: {vib_signal.shape[0]} samples, sample rate = {get_sample_rate('Vib_axial')} Hz")