import os
import subprocess
import pytest
from citadel_local.repo_scan.git_diff import get_changed_files


def _run(cwd, *args):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _make_repo(tmp_path):
    """Create a git repo with an initial commit on main and a feature branch with changes."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "git", "init", "-b", "main")
    _run(repo, "git", "config", "user.email", "test@test.com")
    _run(repo, "git", "config", "user.name", "Test")

    # Initial commit
    (repo / "base.py").write_text("print('hello')\n")
    (repo / "untouched.py").write_text("x = 1\n")
    _run(repo, "git", "add", ".")
    _run(repo, "git", "commit", "-m", "init")

    # Feature branch
    _run(repo, "git", "checkout", "-b", "feature")
    (repo / "new_file.py").write_text("import os\n")
    (repo / "base.py").write_text("print('changed')\n")
    _run(repo, "git", "add", ".")
    _run(repo, "git", "commit", "-m", "feature changes")

    return repo


CFG = {"ignore": [".git"], "max_file_mb": 2}


class TestGetChangedFiles:
    def test_committed_changes(self, tmp_path):
        repo = _make_repo(tmp_path)
        files = get_changed_files(repo, "main", CFG)
        names = {f.name for f in files}
        assert "new_file.py" in names
        assert "base.py" in names
        assert "untouched.py" not in names

    def test_unstaged_changes(self, tmp_path):
        repo = _make_repo(tmp_path)
        (repo / "base.py").write_text("print('unstaged edit')\n")
        files = get_changed_files(repo, "main", CFG)
        assert any(f.name == "base.py" for f in files)

    def test_staged_changes(self, tmp_path):
        repo = _make_repo(tmp_path)
        (repo / "staged.py").write_text("y = 2\n")
        _run(repo, "git", "add", "staged.py")
        files = get_changed_files(repo, "main", CFG)
        assert any(f.name == "staged.py" for f in files)

    def test_ignored_dir_excluded(self, tmp_path):
        repo = _make_repo(tmp_path)
        vendor = repo / "vendor"
        vendor.mkdir()
        (vendor / "lib.py").write_text("vendored\n")
        _run(repo, "git", "add", ".")
        _run(repo, "git", "commit", "-m", "add vendor")

        cfg = {"ignore": [".git", "vendor"], "max_file_mb": 2}
        files = get_changed_files(repo, "main", cfg)
        assert not any("vendor" in str(f) for f in files)

    def test_oversized_file_excluded(self, tmp_path):
        repo = _make_repo(tmp_path)
        big = repo / "big.bin"
        big.write_bytes(b"x" * (3 * 1024 * 1024))  # 3 MB
        _run(repo, "git", "add", "big.bin")
        _run(repo, "git", "commit", "-m", "add big file")

        files = get_changed_files(repo, "main", CFG)
        assert not any(f.name == "big.bin" for f in files)

    def test_not_a_git_repo(self, tmp_path):
        not_repo = tmp_path / "plain"
        not_repo.mkdir()
        with pytest.raises(RuntimeError, match="not a git repository"):
            get_changed_files(not_repo, "main", CFG)

    def test_deleted_file_excluded(self, tmp_path):
        repo = _make_repo(tmp_path)
        os.remove(repo / "base.py")
        _run(repo, "git", "add", "base.py")
        _run(repo, "git", "commit", "-m", "delete base.py")
        files = get_changed_files(repo, "main", CFG)
        assert not any(f.name == "base.py" for f in files)

    def test_returns_absolute_paths(self, tmp_path):
        repo = _make_repo(tmp_path)
        files = get_changed_files(repo, "main", CFG)
        assert all(f.is_absolute() for f in files)
