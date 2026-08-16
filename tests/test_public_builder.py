from pathlib import Path

import pytest

from tools.build_public_release import build


def test_builder_copies_only_allowlisted_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "include.py").write_text("print('ok')\n", encoding="utf-8")
    (source / "private.txt").write_text("not copied\n", encoding="utf-8")
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("include.py -> src/include.py\n", encoding="utf-8")
    target = tmp_path / "target"
    assert build(source, target, allowlist) == 1
    assert (target / "src/include.py").is_file()
    assert not (target / "private.txt").exists()


def test_builder_rejects_notebooks(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "analysis.ipynb").write_text("{}", encoding="utf-8")
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("analysis.ipynb\n", encoding="utf-8")
    with pytest.raises(ValueError, match="denied"):
        build(source, tmp_path / "target", allowlist)


def test_builder_rejects_local_absolute_paths(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "notes.txt").write_text(
        "read /" + "Users/example/private/file.txt\n", encoding="utf-8"
    )
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("notes.txt\n", encoding="utf-8")
    with pytest.raises(ValueError, match="safety scan"):
        build(source, tmp_path / "target", allowlist)


def test_builder_refuses_nonempty_target(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "include.py").write_text("pass\n", encoding="utf-8")
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("include.py\n", encoding="utf-8")
    target = tmp_path / "target"
    target.mkdir()
    (target / "existing.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="not empty"):
        build(source, target, allowlist)
