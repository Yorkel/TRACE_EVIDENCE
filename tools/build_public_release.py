#!/usr/bin/env python3
"""Build a clean public folder from an explicit, file-level allowlist."""

from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
from pathlib import Path


DENIED_NAMES = {
    ".env",
    ".git",
    ".venv",
    ".codex",
    ".claude",
    "CLAUDE.md",
    "KEY_INSIGHTS.md",
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
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "Supabase secret": re.compile(r"\bsb_secret_[A-Za-z0-9_-]{12,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |)PRIVATE KEY-----"),
}
JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")


def parse_allowlist(path: Path) -> list[tuple[str, str]]:
    entries = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        source, marker, destination = line.partition(" -> ")
        entries.append((source, destination if marker else source))
    return entries


def safe_source(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"allowlisted source escapes root: {relative}") from exc
    if not path.is_file():
        raise FileNotFoundError(f"allowlisted source is not a file: {relative}")
    return path


def denied(relative: Path) -> bool:
    return (
        any(part in DENIED_NAMES for part in relative.parts)
        or relative.suffix.lower() in DENIED_SUFFIXES
    )


def jwt_role(token: str) -> str | None:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
    except Exception:
        return None
    role = decoded.get("role")
    return str(role) if role else None


def scan_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    problems = []
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            problems.append(f"{label}: {path.name}")
    for token in JWT.findall(text):
        if jwt_role(token) == "service_role":
            problems.append(f"Supabase service-role JWT: {path.name}")
    local_prefixes = ("/" + "Users/", "/" + "home/")
    if any(prefix in text for prefix in local_prefixes):
        problems.append(f"local absolute path: {path.name}")
    return problems


def build(source_root: Path, target: Path, allowlist: Path) -> int:
    """Copy only reviewed files; refuse existing non-empty targets."""
    source_root = source_root.resolve()
    target = target.resolve()
    if target == source_root or source_root in target.parents:
        raise ValueError("target must be outside the source repository")
    if target.exists() and any(target.iterdir()):
        raise ValueError("target already exists and is not empty")
    target.mkdir(parents=True, exist_ok=True)

    copied = 0
    for source_name, destination_name in parse_allowlist(allowlist):
        source = safe_source(source_root, source_name)
        destination = Path(destination_name)
        if destination.is_absolute() or ".." in destination.parts:
            raise ValueError(f"unsafe destination: {destination_name}")
        if denied(Path(source_name)) or denied(destination):
            raise ValueError(f"denied file in allowlist: {source_name}")
        output = target / destination
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
        copied += 1

    problems = [
        problem
        for path in target.rglob("*")
        if path.is_file()
        for problem in scan_file(path)
    ]
    if problems:
        raise ValueError("public safety scan failed:\n" + "\n".join(problems))
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--allowlist", type=Path, required=True)
    args = parser.parse_args()
    count = build(args.source_root, args.target, args.allowlist)
    print(f"copied {count} reviewed files to {args.target}")


if __name__ == "__main__":
    main()
