import h5py
from pathlib import Path

script_dir = Path(__file__).resolve().parent
file_path = (script_dir / '..' / '..' / '5.Dataset' / 'Experimental Database' / 'struct_rs_R1.mat').resolve()

def print_tree(name, obj, indent=0):
    prefix = "  " * indent
    if isinstance(obj, h5py.Dataset):
        print(f"{prefix}{name}  [Dataset: shape={obj.shape}, dtype={obj.dtype}]")
    else:
        print(f"{prefix}{name}/")

with h5py.File(file_path, 'r') as f:
    def walk(group, indent=0):
        for key in group.keys():
            if key == '#refs#':
                continue  # skip the raw reference dump, we only care about named structure
            item = group[key]
            print_tree(key, item, indent)
            if isinstance(item, h5py.Group):
                walk(item, indent + 1)
    walk(f)
    
    def print_tree(name, obj):
    depth = name.count('/')
    indent = "  " * depth
    kind = "Dataset" if isinstance(obj, h5py.Dataset) else "Group"
    shape_info = f" shape={obj.shape}" if isinstance(obj, h5py.Dataset) else ""
    print(f"{indent}{name.split('/')[-1]}  [{kind}]{shape_info}")