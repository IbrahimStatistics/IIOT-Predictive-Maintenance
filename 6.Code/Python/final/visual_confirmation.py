import h5py
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Fixed project root — independent of where this script lives
PROJECT_ROOT = Path(r'C:\Users\ibrah\OneDrive\Desktop\Btech-Major')
file_path = PROJECT_ROOT / '5.Dataset' / 'Experimental Database' / 'struct_rs_R1.mat'

print("Looking for:", file_path)
print("Exists:", file_path.exists())

with h5py.File(file_path, 'r') as f:
    torque_level = f['rs']['torque05']
    ref = torque_level['Ia'][0, 0]
    ia_repetition1 = f[ref][:]

    signal = ia_repetition1.flatten()
    sample_rate = 55611  # confirmed: 1,001,000 samples / 18s
    time_axis = np.arange(len(signal)) / sample_rate

    # plt.figure(figsize=(12, 4))
    # plt.plot(time_axis, signal)
    # plt.xlabel("Time (s)")
    # plt.ylabel("Current (A)")
    # plt.title("Phase A Current — Healthy Rotor, Torque 0.5 Nm, Repetition 1")
    # plt.tight_layout()
    # plt.show()
    
    plt.figure(figsize=(12, 4))
    plt.plot(time_axis, signal)
    plt.xlim(5.0, 5.05)   # 50ms window — should show ~3 clean sine cycles at 60Hz
    plt.xlabel("Time (s)")
    plt.ylabel("Current (A)")
    plt.title("Phase A Current — Zoomed Steady-State View")
    plt.show()