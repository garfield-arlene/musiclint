#!/usr/bin/env python3
import logging
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, call
from context import __projectpath
from plugins.processMp3 import processMP3Files


@pytest.fixture
def mp3_dir():
    """Creates a temporary directory with a mix of file types."""
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "song1.mp3"), 'w').close()
        open(os.path.join(d, "song2.mp3"), 'w').close()
        open(os.path.join(d, "cover.jpg"), 'w').close()
        open(os.path.join(d, "notes.txt"), 'w').close()
        yield d


@pytest.fixture
def subdir_mp3_dir():
    """Creates a temporary directory tree with mp3s in subdirectories."""
    with tempfile.TemporaryDirectory() as d:
        sub = os.path.join(d, "artist", "album")
        os.makedirs(sub)
        open(os.path.join(d, "root_song.mp3"), 'w').close()
        open(os.path.join(sub, "track1.mp3"), 'w').close()
        open(os.path.join(sub, "track2.mp3"), 'w').close()
        yield d


# --- processMP3Files (no database) ---

@patch("plugins.processMp3.MP3File")
def test_processes_all_mp3_files(mock_mp3, mp3_dir):
    processMP3Files(mp3_dir, 0, None)
    assert mock_mp3.call_count == 2


@patch("plugins.processMp3.MP3File")
def test_skips_non_mp3_files(mock_mp3, mp3_dir):
    processMP3Files(mp3_dir, 0, None)
    processed_paths = [c.args[0] for c in mock_mp3.call_args_list]
    assert all(p.endswith(".mp3") for p in processed_paths)


@patch("plugins.processMp3.MP3File")
def test_processes_mp3s_in_subdirectories(mock_mp3, subdir_mp3_dir):
    processMP3Files(subdir_mp3_dir, 0, None)
    assert mock_mp3.call_count == 3


@patch("plugins.processMp3.MP3File")
def test_empty_directory_no_processing(mock_mp3):
    with tempfile.TemporaryDirectory() as empty_dir:
        processMP3Files(empty_dir, 0, None)
    mock_mp3.assert_not_called()


@patch("plugins.processMp3.MP3File")
def test_verbosity_logs_filenames(mock_mp3, mp3_dir, caplog):
    with caplog.at_level(logging.INFO):
        processMP3Files(mp3_dir, 2, None)
    assert any(".mp3" in record.message for record in caplog.records)


# --- processMP3Files (with database) ---

_DISCOGS_TAGS = {"artist": "X", "album": "Y", "year": "2001",
                 "genre": "Jazz", "song": "T", "track": "2"}
_CHOSEN = {"id": 42, "title": "Y", "year": "2001", "type": "release"}


def _db_patches(mp3_dir, monkeypatch_input='c', find_return=None, fetch_return=None,
                compare_return=None, prompt_return=None):
    '''Return a list of patch targets for database-enabled tests.'''
    if find_return is None:
        find_return = ({"results": [_CHOSEN]}, MagicMock(), "agent/1.0")
    if fetch_return is None:
        fetch_return = _DISCOGS_TAGS
    if compare_return is None:
        compare_return = {}
    if prompt_return is None:
        prompt_return = {}
    return find_return, fetch_return, compare_return, prompt_return


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.find_releases")
@patch("plugins.processMp3._pick_release")
@patch("plugins.processMp3.fetch_release")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags", return_value={})
def test_with_database_authenticates_once(
    mock_compare, mock_display, mock_fetch, mock_pick, mock_find, mock_auth, mock_mp3, mp3_dir, monkeypatch
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_find.return_value = ({"results": [_CHOSEN]}, MagicMock(), "agent/1.0")
    mock_pick.return_value = _CHOSEN
    mock_fetch.return_value = _DISCOGS_TAGS
    monkeypatch.setattr("builtins.input", lambda _: "c")
    processMP3Files(mp3_dir, 0, "discogs")
    mock_auth.assert_called_once()


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.find_releases")
@patch("plugins.processMp3._pick_release")
@patch("plugins.processMp3.fetch_release")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags", return_value={})
def test_with_database_searches_each_file(
    mock_compare, mock_display, mock_fetch, mock_pick, mock_find, mock_auth, mock_mp3, mp3_dir, monkeypatch
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_find.return_value = ({"results": [_CHOSEN]}, MagicMock(), "agent/1.0")
    mock_pick.return_value = _CHOSEN
    mock_fetch.return_value = _DISCOGS_TAGS
    monkeypatch.setattr("builtins.input", lambda _: "c")
    processMP3Files(mp3_dir, 0, "discogs")
    assert mock_find.call_count == 2


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.find_releases")
def test_with_database_handles_no_discogs_result(mock_find, mock_auth, mock_mp3, mp3_dir):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_find.return_value = (None, None, None)
    processMP3Files(mp3_dir, 0, "discogs")  # should not raise


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.find_releases")
@patch("plugins.processMp3._pick_release")
@patch("plugins.processMp3.fetch_release")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags")
@patch("plugins.processMp3.prompt_tag_resolution")
@patch("plugins.processMp3.apply_tags")
def test_with_differences_prompts_and_applies(
    mock_apply, mock_prompt, mock_compare, mock_display,
    mock_fetch, mock_pick, mock_find, mock_auth, mock_mp3, mp3_dir, monkeypatch
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_find.return_value = ({"results": [_CHOSEN]}, MagicMock(), "agent/1.0")
    mock_pick.return_value = _CHOSEN
    mock_fetch.return_value = _DISCOGS_TAGS
    mock_compare.return_value = {"year": {"label": "Year", "file": "2000", "discogs": "2001"}}
    mock_prompt.return_value = {"year": "2001"}
    monkeypatch.setattr("builtins.input", lambda _: "c")
    processMP3Files(mp3_dir, 0, "discogs")
    assert mock_apply.call_count == 2


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.find_releases")
@patch("plugins.processMp3._pick_release")
@patch("plugins.processMp3.fetch_release")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags")
@patch("plugins.processMp3.prompt_tag_resolution")
@patch("plugins.processMp3.apply_tags")
def test_no_apply_when_user_keeps_all_file_values(
    mock_apply, mock_prompt, mock_compare, mock_display,
    mock_fetch, mock_pick, mock_find, mock_auth, mock_mp3, mp3_dir, monkeypatch
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_find.return_value = ({"results": [_CHOSEN]}, MagicMock(), "agent/1.0")
    mock_pick.return_value = _CHOSEN
    mock_fetch.return_value = _DISCOGS_TAGS
    mock_compare.return_value = {"year": {"label": "Year", "file": "2000", "discogs": "2001"}}
    mock_prompt.return_value = {}
    monkeypatch.setattr("builtins.input", lambda _: "c")
    processMP3Files(mp3_dir, 0, "discogs")
    mock_apply.assert_not_called()


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.find_releases")
@patch("plugins.processMp3._pick_release")
@patch("plugins.processMp3.fetch_release")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags", return_value={})
def test_repick_loops_back_on_r_then_continues(
    mock_compare, mock_display, mock_fetch, mock_pick, mock_find, mock_auth, mock_mp3, mp3_dir, monkeypatch
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_find.return_value = ({"results": [_CHOSEN]}, MagicMock(), "agent/1.0")
    mock_pick.return_value = _CHOSEN
    mock_fetch.return_value = _DISCOGS_TAGS
    # First file: user picks 'r' then 'c'; second file: user picks 'c'
    inputs = iter(["r", "c", "c"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    processMP3Files(mp3_dir, 0, "discogs")
    # display_comparison called 3 times total (2 for first file, 1 for second)
    assert mock_display.call_count == 3


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.find_releases")
@patch("plugins.processMp3._pick_release")
@patch("plugins.processMp3.fetch_release")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags", return_value={})
@patch("plugins.processMp3.apply_tags")
def test_skip_skips_file(
    mock_apply, mock_compare, mock_display, mock_fetch, mock_pick, mock_find, mock_auth, mock_mp3, mp3_dir, monkeypatch
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_find.return_value = ({"results": [_CHOSEN]}, MagicMock(), "agent/1.0")
    mock_pick.return_value = _CHOSEN
    mock_fetch.return_value = _DISCOGS_TAGS
    monkeypatch.setattr("builtins.input", lambda _: "s")
    processMP3Files(mp3_dir, 0, "discogs")
    mock_apply.assert_not_called()
