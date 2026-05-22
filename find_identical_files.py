#!/usr/bin/env python3
"""Find files with identical content, and same-named files with differing content."""

import argparse
import hashlib
import shutil
import tokenize
import io
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import yaml


DEFAULT_SCAN_DIR = Path(__file__).parent / "QDSpy"


def hash_bytes(path: Path) -> str:
    h = hashlib.sha256(path.read_bytes())
    return h.hexdigest()


def normalize_python(path: Path) -> str:
    """Return a canonical string for a .py file, stripping comments and normalising whitespace."""
    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        kept = []
        for tok_type, tok_str, *_ in tokens:
            if tok_type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
                            tokenize.ENCODING, tokenize.ENDMARKER):
                continue
            if tok_type == tokenize.STRING and kept and kept[-1] in ("def", "class"):
                # keep docstrings
                kept.append(tok_str)
            elif tok_type == tokenize.STRING and not kept:
                kept.append(tok_str)
            else:
                kept.append(tok_str)
        return " ".join(kept)
    except tokenize.TokenError:
        # fall back to raw hash if file can't be tokenized
        return path.read_text(encoding="utf-8", errors="replace")


def hash_python(path: Path) -> str:
    canonical = normalize_python(path)
    return hashlib.sha256(canonical.encode()).hexdigest()


# Map extension -> hash function
HASHERS: dict[str, Callable[[Path], str]] = {
    ".py":      hash_python,
    ".pickle":  hash_bytes,
    ".jpg":     hash_bytes,
    ".jpeg":    hash_bytes,
    ".png":     hash_bytes,
    ".txt":     hash_bytes,
}


def _collect_digests(scan_dirs: list[Path]) -> dict[str, dict[Path, str]]:
    """Return {ext: {path: digest}} for all known-extension files under scan_dirs."""
    by_ext: dict[str, dict[Path, str]] = defaultdict(dict)
    for scan_dir in scan_dirs:
        for path in sorted(scan_dir.rglob("*")):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            hasher = HASHERS.get(ext)
            if hasher is None:
                continue
            by_ext[ext][path] = hasher(path)
    return by_ext


def find_identical(by_ext: dict[str, dict[Path, str]]) -> dict[str, list[list[Path]]]:
    """Files that share the same digest (identical content), grouped by extension."""
    result: dict[str, list[list[Path]]] = {}
    for ext, path_digest in sorted(by_ext.items()):
        digest_to_paths: dict[str, list[Path]] = defaultdict(list)
        for path, digest in path_digest.items():
            digest_to_paths[digest].append(path)
        groups = [paths for paths in digest_to_paths.values() if len(paths) > 1]
        if groups:
            result[ext] = groups
    return result


def find_same_name_different_content(by_ext: dict[str, dict[Path, str]]) -> list[list[Path]]:
    """Files that share a filename but have different content (across any subdirectory)."""
    name_to_paths: dict[str, list[Path]] = defaultdict(list)
    for path_digest in by_ext.values():
        for path in path_digest:
            name_to_paths[path.name].append(path)

    conflicts: list[list[Path]] = []
    for paths in name_to_paths.values():
        if len(paths) < 2:
            continue
        # retrieve digest for each path (extension must match since name includes it)
        ext = paths[0].suffix.lower()
        digests = {p: by_ext[ext][p] for p in paths}
        if len(set(digests.values())) > 1:
            conflicts.append(sorted(paths))
    return conflicts


COLLECT_EXTS = {".py", ".txt"}
OUTPUT_ROOT = Path(__file__).parent / "same_name_different_content"


def collect_conflicts(
    conflicts: list[list[Path]],
    by_ext: dict[str, dict[Path, str]],
    duplicates: dict[str, list[list[Path]]],
    root: Path,
) -> None:
    """Copy same-name/different-content .py and .txt files into a timestamped output folder."""
    relevant = [g for g in conflicts if g[0].suffix.lower() in COLLECT_EXTS]
    if not relevant:
        print("Nothing to collect.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    run_dir = OUTPUT_ROOT / timestamp
    if run_dir.exists():
        raise FileExistsError(f"Output folder already exists: {run_dir}")
    run_dir.mkdir(parents=True)

    conflict_records: dict = {}

    for group in relevant:
        ext = group[0].suffix.lower()
        stem = group[0].stem
        ext_label = ext.lstrip(".")
        group_dir = run_dir / f"{stem}_{ext_label}"

        # Group paths by digest so A≡C → one version, B → another version
        digest_to_paths: dict[str, list[Path]] = defaultdict(list)
        for p in group:
            digest_to_paths[by_ext[ext][p]].append(p)

        version_info: dict = {}
        for v_idx, (digest, paths) in enumerate(digest_to_paths.items(), 1):
            version = f"v{v_idx:02d}"
            dest_dir = group_dir / version
            dest_dir.mkdir(parents=True)
            # copy one representative file
            shutil.copy2(paths[0], dest_dir / paths[0].name)
            version_info[version] = {
                "digest": digest,
                "sources": [str(p.resolve()) for p in paths],
            }

        conflict_records[group[0].name] = version_info

    # Build full comparison summary for the YAML
    identical_summary: dict = {}
    for ext, groups in duplicates.items():
        identical_summary[ext] = [
            [str(p.relative_to(root)) for p in grp] for grp in groups
        ]

    conflict_summary: dict = {}
    for group in conflicts:
        ext = group[0].suffix.lower()
        conflict_summary[group[0].name] = {
            str(p.relative_to(root)): by_ext[ext][p][:8] for p in group
        }

    report = {
        "scanned_root": str(root),
        "timestamp": timestamp,
        "identical_content": identical_summary,
        "same_name_different_content": conflict_summary,
        "collected": conflict_records,
    }

    yaml_path = run_dir / "sources.yaml"
    with yaml_path.open("w", encoding="utf-8") as fh:
        yaml.dump(report, fh, allow_unicode=True, sort_keys=True)

    print(f"Collected {len(relevant)} conflict group(s) → {run_dir}")
    print(f"Full report in {yaml_path.name}")


def _common_root(dirs: list[Path]) -> Path:
    """Longest common ancestor of all given directories."""
    parts_list = [d.parts for d in dirs]
    common = []
    for level in zip(*parts_list):
        if len(set(level)) == 1:
            common.append(level[0])
        else:
            break
    return Path(*common) if common else Path("/")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folders", nargs="*", type=Path,
                        help="Directories to scan (default: QDSpy/)")
    parser.add_argument("--collect", action="store_true",
                        help="Copy .py/.txt conflicts into same_name_different_content/")
    args = parser.parse_args()
    scan_dirs: list[Path] = [p.resolve() for p in args.folders] or [DEFAULT_SCAN_DIR]

    root = _common_root(scan_dirs)

    by_ext = _collect_digests(scan_dirs)
    duplicates = find_identical(by_ext)
    conflicts = find_same_name_different_content(by_ext)

    if not duplicates:
        print("No identical files found.")
    else:
        print("=== IDENTICAL CONTENT ===")
        for ext, groups in duplicates.items():
            print(f"\n  [{ext}]")
            for i, group in enumerate(groups, 1):
                print(f"  Group {i}:")
                for p in group:
                    print(f"    {p.relative_to(root)}")

    print()
    if not conflicts:
        print("No same-name / different-content files found.")
    else:
        print("=== SAME NAME, DIFFERENT CONTENT ===")
        for group in conflicts:
            print(f"\n  {group[0].name}")
            ext = group[0].suffix.lower()
            for p in group:
                digest = by_ext[ext][p]
                print(f"    {p.relative_to(root)}  [{digest[:8]}...]")

    if args.collect:
        print()
        collect_conflicts(conflicts, by_ext, duplicates, root)


if __name__ == "__main__":
    main()
