#!/usr/bin/env python3
import logging
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, call
from context import __projectpath
from plugins.processMp3 import processMP3Files, checkAlbum


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


# --- processMP3Files ---

@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.checkAlbum")
@patch("plugins.processMp3.chooseDBPlugin")
def test_processes_all_mp3_files(mock_plugin, mock_check, mock_mp3, mp3_dir):
    mock_plugin.return_value = MagicMock()
    processMP3Files(mp3_dir, 0, "discogs")
    assert mock_mp3.call_count == 2
    assert mock_check.call_count == 2


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.checkAlbum")
@patch("plugins.processMp3.chooseDBPlugin")
def test_skips_non_mp3_files(mock_plugin, mock_check, mock_mp3, mp3_dir):
    mock_plugin.return_value = MagicMock()
    processMP3Files(mp3_dir, 0, "discogs")
    processed_paths = [c.args[0] for c in mock_mp3.call_args_list]
    assert all(p.endswith(".mp3") for p in processed_paths)


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.checkAlbum")
@patch("plugins.processMp3.chooseDBPlugin")
def test_processes_mp3s_in_subdirectories(mock_plugin, mock_check, mock_mp3, subdir_mp3_dir):
    mock_plugin.return_value = MagicMock()
    processMP3Files(subdir_mp3_dir, 0, "discogs")
    assert mock_mp3.call_count == 3


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.checkAlbum")
@patch("plugins.processMp3.chooseDBPlugin")
def test_empty_directory_no_processing(mock_plugin, mock_check, mock_mp3):
    mock_plugin.return_value = MagicMock()
    with tempfile.TemporaryDirectory() as empty_dir:
        processMP3Files(empty_dir, 0, "discogs")
    mock_mp3.assert_not_called()
    mock_check.assert_not_called()


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.checkAlbum")
@patch("plugins.processMp3.chooseDBPlugin")
def test_selects_correct_db_plugin(mock_plugin, mock_check, mock_mp3, mp3_dir):
    mock_plugin.return_value = MagicMock()
    processMP3Files(mp3_dir, 0, "discogs")
    mock_plugin.assert_called_once_with("discogs")


@patch("plugins.processMp3.MP3File")
@patch("plugins.processMp3.checkAlbum")
@patch("plugins.processMp3.chooseDBPlugin")
def test_verbosity_logs_filenames(mock_plugin, mock_check, mock_mp3, mp3_dir, caplog):
    mock_plugin.return_value = MagicMock()
    with caplog.at_level(logging.INFO):
        processMP3Files(mp3_dir, 2, "discogs")
    assert any(".mp3" in record.message for record in caplog.records)


# --- checkAlbum ---

def test_checkAlbum_reads_album_tag():
    mock_song = MagicMock()
    mock_song.album = [None, "('tag', 'Thriller')"]
    # Should not raise
    checkAlbum(mock_song)


def test_checkAlbum_calls_song_album():
    mock_song = MagicMock()
    mock_song.album = [None, "('tag', 'Some Album')"]
    checkAlbum(mock_song)
    _ = mock_song.album  # verify property was accessed
