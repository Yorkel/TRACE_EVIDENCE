"""Path-safe, hash-bound release manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ManifestError(ValueError):
    """Raised when a manifest or one of its bound files is invalid."""


@dataclass(frozen=True)
class ValidatedRelease:
    manifest: dict[str, Any]
    manifest_path: Path
    files: dict[str, Path]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_repo_file(repo_root: Path, relative_path: str) -> Path:
    relative = Path(relative_path)
    if relative.is_absolute():
        raise ManifestError(f"path must be repository-relative: {relative_path}")
    root = repo_root.resolve()
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ManifestError(f"path escapes repository: {relative_path}") from exc
    if not resolved.is_file():
        raise ManifestError(f"bound file does not exist: {relative_path}")
    return resolved


def validate_manifest(manifest_path: Path, repo_root: Path) -> ValidatedRelease:
    """Validate schema, status, safe paths and every declared SHA-256."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ManifestError("manifest schema_version must be 1")
    if manifest.get("status") not in {"candidate", "approved"}:
        raise ManifestError("manifest status must be candidate or approved")
    if not manifest.get("snapshot_id"):
        raise ManifestError("manifest snapshot_id is required")
    declared = manifest.get("files")
    if not isinstance(declared, dict) or not declared:
        raise ManifestError("manifest files must be a non-empty path-to-hash object")

    validated: dict[str, Path] = {}
    for relative_path, expected in sorted(declared.items()):
        if not isinstance(expected, str) or len(expected) != 64:
            raise ManifestError(f"invalid SHA-256 for {relative_path}")
        path = safe_repo_file(repo_root, relative_path)
        actual = sha256_file(path)
        if actual != expected:
            raise ManifestError(f"SHA-256 mismatch: {relative_path}")
        validated[relative_path] = path
    return ValidatedRelease(manifest, manifest_path.resolve(), validated)


def candidate_manifest(
    repo_root: Path,
    snapshot_id: str,
    relative_files: list[str],
) -> dict[str, Any]:
    """Construct an unapproved candidate manifest from an explicit file list."""
    if not snapshot_id.strip():
        raise ValueError("snapshot_id must not be empty")
    if not relative_files:
        raise ValueError("at least one file must be bound")
    files = {}
    for relative_path in sorted(set(relative_files)):
        path = safe_repo_file(repo_root, relative_path)
        files[relative_path] = sha256_file(path)
    return {
        "schema_version": 1,
        "snapshot_id": snapshot_id,
        "status": "candidate",
        "approval": {"approved_by": None, "approved_at": None},
        "files": files,
    }
