#!/usr/bin/env python3
import os
import pytest
import tempfile
from context import __projectpath
from plugins.cliArgs import cliArgs


@pytest.fixture
def cli():
    return cliArgs()


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


# --- readable_dir ---

def test_readable_dir_valid(cli, tmp_dir):
    result = cli.readable_dir(tmp_dir)
    assert result == tmp_dir


def test_readable_dir_invalid_path(cli):
    with pytest.raises(Exception, match="is not a valid path"):
        cli.readable_dir("/nonexistent/path/abc123")


def test_readable_dir_rejects_file(cli, tmp_dir):
    file_path = os.path.join(tmp_dir, "not_a_dir.txt")
    open(file_path, 'w').close()
    with pytest.raises(Exception, match="is not a valid path"):
        cli.readable_dir(file_path)


# --- usableDB ---

def test_usableDB_valid_discogs(cli):
    result = cli.usableDB("discogs")
    assert result == "discogs"


def test_usableDB_invalid(cli):
    with pytest.raises(Exception, match="is not a valid DB"):
        cli.usableDB("napster")


def test_usableDB_case_sensitive(cli):
    with pytest.raises(Exception, match="is not a valid DB"):
        cli.usableDB("Discogs")


def test_usableDB_empty_string(cli):
    with pytest.raises(Exception, match="is not a valid DB"):
        cli.usableDB("")


# --- args property ---

def test_args_returns_namespace(cli, monkeypatch):
    monkeypatch.setattr("sys.argv", ["musiclint.py"])
    args = cli.args
    assert hasattr(args, "library")
    assert hasattr(args, "verbosity")
    assert hasattr(args, "database")
    assert hasattr(args, "mp3")


def test_args_mp3_flag_default_false(cli, monkeypatch):
    monkeypatch.setattr("sys.argv", ["musiclint.py"])
    args = cli.args
    assert args.mp3 is False


def test_args_mp3_flag_set(cli, monkeypatch):
    monkeypatch.setattr("sys.argv", ["musiclint.py", "-m"])
    args = cli.args
    assert args.mp3 is True


def test_args_verbosity_default_zero(cli, monkeypatch):
    monkeypatch.setattr("sys.argv", ["musiclint.py"])
    args = cli.args
    assert args.verbosity == 0


def test_args_verbosity_count(cli, monkeypatch):
    monkeypatch.setattr("sys.argv", ["musiclint.py", "-v", "-v"])
    args = cli.args
    assert args.verbosity == 2


def test_args_library_set(cli, monkeypatch, tmp_dir):
    monkeypatch.setattr("sys.argv", ["musiclint.py", "-l", tmp_dir])
    args = cli.args
    assert args.library == tmp_dir


def test_args_database_set(cli, monkeypatch):
    monkeypatch.setattr("sys.argv", ["musiclint.py", "-d", "discogs"])
    args = cli.args
    assert args.database == "discogs"
