#!/usr/bin/env python3
"""Find files with identical content, and same-named files with differing content."""

import hashlib
import tokenize
import io
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path


SCAN_DIR = Path(__file__).parent / "QDSpy"


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


def _collect_digests(scan_dir: Path) -> dict[str, dict[Path, str]]:
    """Return {ext: {path: digest}} for all known-extension files under scan_dir."""
    by_ext: dict[str, dict[Path, str]] = defaultdict(dict)
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


def main():
    by_ext = _collect_digests(SCAN_DIR)
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
                    print(f"    {p.relative_to(SCAN_DIR.parent)}")

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
                print(f"    {p.relative_to(SCAN_DIR.parent)}  [{digest[:8]}...]")


if __name__ == "__main__":
    main()
