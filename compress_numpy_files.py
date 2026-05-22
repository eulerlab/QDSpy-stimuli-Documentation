import argparse
from pathlib import Path
import numpy as np


def compress_npy_files(root: Path, delete_originals: bool = False) -> None:
    npy_files = [
        p for p in root.rglob("*.npy")
        if "QDSpyExport" in p.parts
    ]

    if not npy_files:
        print("No .npy files found in any QDSpyExport folder.")
        return

    for npy_path in sorted(npy_files):
        npz_path = npy_path.with_suffix(".npz")
        key = npy_path.stem
        data = np.load(npy_path)
        np.savez_compressed(npz_path, data=data)
        size_npy = npy_path.stat().st_size
        size_npz = npz_path.stat().st_size
        ratio = size_npz / size_npy * 100
        print(f"{npy_path.relative_to(root)}  →  {npz_path.name}  "
              f"({size_npy // 1024} KB → {size_npz // 1024} KB, {ratio:.1f}%)")
        if delete_originals:
            npy_path.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compress .npy files in QDSpyExport folders to .npz."
    )
    parser.add_argument(
        "--root", default=".", help="Repository root to search from (default: .)"
    )
    parser.add_argument(
        "--delete", action="store_true",
        help="Delete original .npy files after compression."
    )
    args = parser.parse_args()

    compress_npy_files(Path(args.root).resolve(), delete_originals=args.delete)
