#!/usr/bin/env python3
"""Generate a deterministic MD5 manifest for the repository."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Iterable, Tuple

EXCLUDED_FILES = {"md5.txt", "md5_current.txt"}
EXCLUDED_PREFIXES = (".git/",)
CHUNK_SIZE = 1024 * 1024  # 1 MiB


def iter_files(root: Path) -> Iterable[Tuple[str, Path]]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root).as_posix()
        if rel_path in EXCLUDED_FILES:
            continue
        if any(rel_path.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            continue
        yield rel_path, path


def md5_for_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(root: Path) -> str:
    entries = []
    for rel_path, full_path in sorted(iter_files(root)):
        entries.append(f"{md5_for_file(full_path)}  {rel_path}")
    return "\n".join(entries) + ("\n" if entries else "")


def write_output(key: str, value: str) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if not output_file:
        return
    with open(output_file, "a", encoding="utf-8") as fh:
        fh.write(f"{key}={value}\n")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    manifest_text = build_manifest(repo_root)
    manifest_path = repo_root / "md5.txt"

    if manifest_path.exists():
        current_text = manifest_path.read_text(encoding="utf-8")
        if current_text == manifest_text:
            print("No MD5 changes detected.")
            write_output("md5_changed", "false")
            return

    manifest_path.write_text(manifest_text, encoding="utf-8")
    print(f"Updated {manifest_path.relative_to(repo_root)} with latest checksums.")
    write_output("md5_changed", "true")


if __name__ == "__main__":
    main()
