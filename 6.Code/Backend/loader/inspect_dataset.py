from pathlib import Path
import h5py

script_dir = Path(__file__).resolve().parent

file_path = (script_dir/".."/".."/".."/"5.Dataset"/"Experimental Database"/"struct_rs_R1.mat").resolve()

print(file_path)   # Always print it while debugging

with h5py.File(file_path, "r") as f:
    torque_level = f["rs"]["torque05"]
    ref = torque_level["Ia"][0, 0]
    ia_repetition1 = f[ref][:]

print("Shape:", ia_repetition1.shape)
print("Dtype:", ia_repetition1.dtype)
print("First 10 values:", ia_repetition1[:10].flatten())