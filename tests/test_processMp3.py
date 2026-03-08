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

@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.search_track")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags", return_value={})
def test_with_database_authenticates_once(
    mock_compare, mock_display, mock_search, mock_auth, mock_mp3, mp3_dir
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_search.return_value = {"artist": "A", "album": "B", "year": "2000",
                                "genre": "Rock", "song": "S", "track": "1"}
    processMP3Files(mp3_dir, 0, "discogs")
    mock_auth.assert_called_once()


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.search_track")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags", return_value={})
def test_with_database_searches_each_file(
    mock_compare, mock_display, mock_search, mock_auth, mock_mp3, mp3_dir
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_search.return_value = {"artist": "A", "album": "B", "year": "2000",
                                "genre": "Rock", "song": "S", "track": "1"}
    processMP3Files(mp3_dir, 0, "discogs")
    assert mock_search.call_count == 2


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.search_track", return_value=None)
def test_with_database_handles_no_discogs_result(mock_search, mock_auth, mock_mp3, mp3_dir):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    # Should not raise when Discogs returns nothing
    processMP3Files(mp3_dir, 0, "discogs")


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.search_track")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags")
@patch("plugins.processMp3.prompt_tag_resolution")
@patch("plugins.processMp3.apply_tags")
def test_with_differences_prompts_and_applies(
    mock_apply, mock_prompt, mock_compare, mock_display,
    mock_search, mock_auth, mock_mp3, mp3_dir
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    discogs = {"artist": "X", "album": "Y", "year": "2001",
               "genre": "Jazz", "song": "T", "track": "2"}
    mock_search.return_value = discogs
    mock_compare.return_value = {"year": {"label": "Year", "file": "2000", "discogs": "2001"}}
    mock_prompt.return_value = {"year": "2001"}

    processMP3Files(mp3_dir, 0, "discogs")

    assert mock_prompt.call_count == 2
    assert mock_apply.call_count == 2


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.authDiscogs")
@patch("plugins.processMp3.search_track")
@patch("plugins.processMp3.display_comparison")
@patch("plugins.processMp3.compare_tags")
@patch("plugins.processMp3.prompt_tag_resolution")
@patch("plugins.processMp3.apply_tags")
def test_no_apply_when_user_keeps_all_file_values(
    mock_apply, mock_prompt, mock_compare, mock_display,
    mock_search, mock_auth, mock_mp3, mp3_dir
):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")
    mock_search.return_value = {"artist": "X", "album": "Y", "year": "2001",
                                "genre": "Jazz", "song": "T", "track": "2"}
    mock_compare.return_value = {"year": {"label": "Year", "file": "2000", "discogs": "2001"}}
    mock_prompt.return_value = {}  # user made no changes

    processMP3Files(mp3_dir, 0, "discogs")
    mock_apply.assert_not_called()
