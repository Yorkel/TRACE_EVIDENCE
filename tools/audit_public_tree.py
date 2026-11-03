#!/usr/bin/env python3
"""Fail a public-tree audit on excluded material or missing release metadata."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from tools.build_public_release import SECRET_PATTERNS, JWT, jwt_role


DENIED_PARTS = {
    ".codex",
    ".claude",
    ".mypy_cache",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dashboard",
    "dist",
    "notebooks",
    "outputs",
    "releases",
}
DENIED_NAMES = {
    "CLAUDE.md",
    "KEY_INSIGHTS.md",
    ".coverage",
}
DENIED_SUFFIXES = {
    ".csv",
    ".docx",
    ".ipynb",
    ".jsonl",
    ".npy",
    ".npz",
    ".parquet",
    ".pdf",
    ".pptx",
    ".safetensors",
    ".xlsx",
    ".zip",
}
WITHDRAWN_PATTERNS = {
    "withdrawn three-registers framing": re.compile(
        "three systems " + "foreground|three national " + "registers|policy " + "registers",
        re.I,
    ),
    "withdrawn association statistic": re.compile("Cram" + "er", re.I),
}
SEPTEMBER_REVIEWED = {'evidence/september_2026.json': '5c1ff8ecf8a6f2e11ac085d7782d4954c715ef6933416f59e8f82a48d2cd2257', 'tools/verify_september.py': '3378c0477506c4dc6aef205f76be1afab281c01c14e268c2598e8de94c4f9643'}
LOCAL_PREFIXES = ("/" + "Users/", "/" + "home/")


def audit(root: Path) -> list[str]:
    problems = []
    required = {
        "LICENSE",
        "README.md",
    }
    for name in sorted(required):
        if not (root / name).is_file():
            problems.append(f"missing required file: {name}")

    for path in root.rglob("*"):
        if path.is_symlink():
            problems.append(f"symbolic link not allowed: {path.relative_to(root)}")
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if ".git" in relative.parts:
            continue
        if path.name in DENIED_NAMES:
            problems.append(f"denied file: {relative}")
        if set(relative.parts) & DENIED_PARTS or any(
            part.endswith(".egg-info") for part in relative.parts
        ):
            problems.append(f"denied path: {relative}")
        if path.suffix.lower() in DENIED_SUFFIXES:
            problems.append(f"denied suffix: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            problems.append(f"unreviewed binary file: {relative}")
            continue
        if any(prefix in text for prefix in LOCAL_PREFIXES):
            problems.append(f"local absolute path: {relative}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                problems.append(f"{label}: {relative}")
        for token in JWT.findall(text):
            if jwt_role(token) == "service_role":
                problems.append(f"Supabase service-role JWT: {relative}")
        for label, pattern in WITHDRAWN_PATTERNS.items():
            if (label == "withdrawn association statistic"
                    and relative.as_posix() in SEPTEMBER_REVIEWED):
                # The September registry is a new verified population, not the
                # withdrawn historical association. Its integrity is checked in CI.
                import hashlib
                if hashlib.sha256(path.read_bytes()).hexdigest() == SEPTEMBER_REVIEWED[relative.as_posix()]:
                    continue
            if pattern.search(text):
                problems.append(f"{label}: {relative}")
        if path.suffix == ".json" and '"cells"' in text and '"metadata"' in text:
            problems.append(f"notebook-like JSON: {relative}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    args = parser.parse_args()
    problems = audit(args.root.resolve())
    if problems:
        raise SystemExit("public audit failed:\n- " + "\n- ".join(problems))
    print("public audit passed")


if __name__ == "__main__":
    main()
