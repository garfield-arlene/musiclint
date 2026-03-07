#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock
from context import __projectpath


# --- main() ---

@patch("plugins.processMp3.processMP3Files")
@patch("plugins.logIT.logIT")
def test_main_calls_processMP3Files_when_mp3_flag_set(mock_log, mock_process, monkeypatch):
    monkeypatch.setattr("sys.argv", ["musiclint.py", "-m", "-l", "/tmp"])
    import importlib
    import musiclint
    importlib.reload(musiclint)

    mock_args = MagicMock()
    mock_args.mp3 = True
    mock_args.database = None
    mock_args.library = "/tmp"
    mock_args.verbosity = 0

    with patch("musiclint.args", mock_args), \
         patch("musiclint.logger", MagicMock()), \
         patch("plugins.processMp3.processMP3Files") as mock_proc:
        musiclint.main()
        mock_proc.assert_called_once_with("/tmp", 0, None)


@patch("plugins.processMp3.processMP3Files")
def test_main_does_not_call_processMP3Files_when_mp3_flag_not_set(mock_process, monkeypatch):
    import importlib
    import musiclint
    importlib.reload(musiclint)

    mock_args = MagicMock()
    mock_args.mp3 = False
    mock_args.database = None
    mock_args.library = "/tmp"
    mock_args.verbosity = 0

    with patch("musiclint.args", mock_args), \
         patch("musiclint.logger", MagicMock()):
        musiclint.main()
        mock_process.assert_not_called()


def test_main_imports_queryDiscogs_when_database_set(monkeypatch):
    import importlib
    import musiclint
    importlib.reload(musiclint)

    mock_args = MagicMock()
    mock_args.mp3 = False
    mock_args.database = "discogs"
    mock_args.library = "/tmp"
    mock_args.verbosity = 0

    with patch("musiclint.args", mock_args), \
         patch("musiclint.logger", MagicMock()), \
         patch("builtins.print") as mock_print:
        musiclint.main()
        mock_print.assert_called_with("Using Discogs.com for online DB\n")
