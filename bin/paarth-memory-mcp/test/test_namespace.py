"""Tests for git-root namespace isolation."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from memory_os.namespace import GLOBAL_NAMESPACE, friendly_name, git_root, namespace_for


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)


def test_two_repos_get_different_namespaces(tmp_path: Path) -> None:
    repo_a = tmp_path / "alpha"
    repo_b = tmp_path / "bravo"
    repo_a.mkdir()
    repo_b.mkdir()
    _init_git_repo(repo_a)
    _init_git_repo(repo_b)

    ns_a = namespace_for(repo_a)
    ns_b = namespace_for(repo_b)

    assert ns_a != ns_b
    assert len(ns_a) == 16
    assert len(ns_b) == 16


def test_subdirectory_inherits_repo_namespace(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    deep = repo / "src" / "deep" / "nested"
    deep.mkdir(parents=True)

    assert namespace_for(repo) == namespace_for(deep)


def test_namespace_is_stable(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    assert namespace_for(repo) == namespace_for(repo)


def test_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PAARTH_MEMORY_NAMESPACE", "my-custom-ns")
    assert namespace_for(tmp_path) == "my-custom-ns"


def test_non_git_dir_uses_path_hash(tmp_path: Path) -> None:
    # No git init — should still return a deterministic namespace
    other = tmp_path / "no-git"
    other.mkdir()
    ns = namespace_for(other)
    assert ns
    assert len(ns) == 16


def test_git_root_returns_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    root = git_root(repo)
    assert root is not None
    assert root.resolve() == repo.resolve()


def test_friendly_name_uses_repo_dir(tmp_path: Path) -> None:
    repo = tmp_path / "my-project"
    repo.mkdir()
    _init_git_repo(repo)
    assert friendly_name(repo) == "my-project"


def test_global_namespace_constant() -> None:
    assert GLOBAL_NAMESPACE == "__global__"
