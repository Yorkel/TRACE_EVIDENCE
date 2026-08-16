import json

import pytest

from trace_evidence.release import (
    ManifestError,
    candidate_manifest,
    validate_manifest,
)


def test_candidate_binds_only_explicit_files(tmp_path):
    (tmp_path / "included.txt").write_text("included", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("ignored", encoding="utf-8")
    manifest = candidate_manifest(tmp_path, "example-1", ["included.txt"])
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    validated = validate_manifest(manifest_path, tmp_path)
    assert list(validated.files) == ["included.txt"]


def test_changed_file_breaks_validation(tmp_path):
    target = tmp_path / "evidence.txt"
    target.write_text("first", encoding="utf-8")
    manifest = candidate_manifest(tmp_path, "example-2", ["evidence.txt"])
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    target.write_text("changed", encoding="utf-8")
    with pytest.raises(ManifestError, match="SHA-256 mismatch"):
        validate_manifest(manifest_path, tmp_path)


def test_path_escape_is_rejected(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    with pytest.raises(ManifestError, match="escapes"):
        candidate_manifest(tmp_path, "example-3", ["../outside.txt"])
