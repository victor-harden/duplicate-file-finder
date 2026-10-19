#!/usr/bin/env python3
"""Find duplicate files by size and SHA-256."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path


def sha256_file(path: Path, chunk: int = 65536) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_files(paths):
    for root in paths:
        if root.is_file():
            yield root
            continue
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                yield path


def find_duplicates(paths):
    by_size = defaultdict(list)
    for path in iter_files(paths):
        try:
            by_size[path.stat().st_size].append(path)
        except OSError:
            continue

    groups = []
    for size, candidates in by_size.items():
        if len(candidates) < 2:
            continue
        by_hash = defaultdict(list)
        for path in candidates:
            try:
                by_hash[sha256_file(path)].append(path)
            except OSError:
                continue
        for digest, files in by_hash.items():
            if len(files) > 1:
                files = sorted(files)
                groups.append({
                    "sha256": digest,
                    "size": size,
                    "files": [str(p) for p in files],
                    "wasted_bytes": size * (len(files) - 1),
                })
    groups.sort(key=lambda g: g["wasted_bytes"], reverse=True)
    return groups


def delete_duplicates(groups):
    removed = []
    for group in groups:
        for path_string in group["files"][1:]:
            path = Path(path_string)
            try:
                path.unlink()
                removed.append(path_string)
            except OSError as exc:
                print(f"cannot remove {path}: {exc}", file=sys.stderr)
    return removed


def human(size: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1000 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1000
    return f"{size:.1f} TB"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Find duplicate files")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--delete", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args(argv)

    missing = [str(p) for p in args.paths if not p.exists()]
    if missing:
        print(f"missing paths: {', '.join(missing)}", file=sys.stderr)
        return 2

    groups = find_duplicates(args.paths)
    payload = {"groups": groups,
               "duplicate_files": sum(len(g["files"]) - 1 for g in groups),
               "wasted_bytes": sum(g["wasted_bytes"] for g in groups)}
    if args.delete:
        if not args.yes:
            print(f"will delete {payload['duplicate_files']} file(s); re-run with --yes",
                  file=sys.stderr)
            return 1
        payload["removed"] = delete_duplicates(groups)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for group in groups:
            print(f"{human(group['size'])} each, {len(group['files'])} copies:")
            for path in group["files"]:
                print(f"  {path}")
        print(f"\nduplicate files: {payload['duplicate_files']}, "
              f"wasted space: {human(payload['wasted_bytes'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
