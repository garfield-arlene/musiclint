#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock
from context import __projectpath
import musiclint


# --- main() ---

def test_main_calls_processMP3Files_when_mp3_flag_set(monkeypatch):
    mock_args = MagicMock()
    mock_args.mp3 = True
    mock_args.database = None
    mock_args.library = "/tmp"
    mock_args.verbosity = 0

    monkeypatch.setattr(musiclint, "args", mock_args, raising=False)
    monkeypatch.setattr(musiclint, "logger", MagicMock(), raising=False)

    with patch("plugins.processMp3.processMP3Files") as mock_proc:
        musiclint.main()
        mock_proc.assert_called_once_with("/tmp", 0, None)


def test_main_does_not_call_processMP3Files_when_mp3_flag_not_set(monkeypatch):
    mock_args = MagicMock()
    mock_args.mp3 = False
    mock_args.database = None
    mock_args.library = "/tmp"
    mock_args.verbosity = 0

    monkeypatch.setattr(musiclint, "args", mock_args, raising=False)
    monkeypatch.setattr(musiclint, "logger", MagicMock(), raising=False)

    with patch("plugins.processMp3.processMP3Files") as mock_proc:
        musiclint.main()
        mock_proc.assert_not_called()


def test_main_prints_discogs_notice_when_database_set(monkeypatch):
    mock_args = MagicMock()
    mock_args.mp3 = False
    mock_args.database = "discogs"
    mock_args.library = "/tmp"
    mock_args.verbosity = 0

    monkeypatch.setattr(musiclint, "args", mock_args, raising=False)
    monkeypatch.setattr(musiclint, "logger", MagicMock(), raising=False)

    with patch("builtins.print") as mock_print:
        musiclint.main()
        mock_print.assert_called_with("Using Discogs.com for online DB\n")
