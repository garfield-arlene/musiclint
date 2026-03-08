#!/usr/bin/env python3
import pytest
from unittest.mock import MagicMock, patch, call
from context import __projectpath
from plugins.compareAndEdit import (
    compare_tags,
    prompt_tag_resolution,
    apply_tags,
    display_comparison,
)

FILE_TAGS = {
    'song':   'My Track',
    'artist': 'Some Artist',
    'album':  'Some Album',
    'year':   '2000',
    'track':  '1',
    'genre':  'Electronic',
}

DISCOGS_TAGS = {
    'song':   'My Track',
    'artist': 'Some Artist',
    'album':  'Some Album',
    'year':   '2001',
    'track':  '1',
    'genre':  'House',
}


# --- compare_tags ---

def test_compare_tags_detects_differences():
    diffs = compare_tags(FILE_TAGS, DISCOGS_TAGS)
    assert 'year' in diffs
    assert 'genre' in diffs


def test_compare_tags_ignores_matching_tags():
    diffs = compare_tags(FILE_TAGS, DISCOGS_TAGS)
    assert 'song' not in diffs
    assert 'artist' not in diffs
    assert 'album' not in diffs
    assert 'track' not in diffs


def test_compare_tags_returns_file_and_discogs_values():
    diffs = compare_tags(FILE_TAGS, DISCOGS_TAGS)
    assert diffs['year']['file'] == '2000'
    assert diffs['year']['discogs'] == '2001'


def test_compare_tags_empty_when_all_match():
    diffs = compare_tags(FILE_TAGS, FILE_TAGS.copy())
    assert diffs == {}


def test_compare_tags_treats_none_as_empty():
    file_tags = {**FILE_TAGS, 'genre': None}
    discogs_tags = {**DISCOGS_TAGS, 'genre': ''}
    diffs = compare_tags(file_tags, discogs_tags)
    assert 'genre' not in diffs


def test_compare_tags_strips_whitespace():
    file_tags = {**FILE_TAGS, 'year': '  2001  '}
    discogs_tags = {**DISCOGS_TAGS, 'year': '2001'}
    diffs = compare_tags(file_tags, discogs_tags)
    assert 'year' not in diffs


def test_compare_tags_includes_label():
    diffs = compare_tags(FILE_TAGS, DISCOGS_TAGS)
    assert diffs['year']['label'] == 'Year'
    assert diffs['genre']['label'] == 'Genre'


# --- prompt_tag_resolution ---

def test_prompt_returns_empty_when_no_differences():
    result = prompt_tag_resolution({})
    assert result == {}


def test_prompt_keep_file_value(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: 'f')
    diffs = {'year': {'label': 'Year', 'file': '2000', 'discogs': '2001'}}
    result = prompt_tag_resolution(diffs)
    assert result['year'] == '2000'


def test_prompt_use_discogs_value(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: 'd')
    diffs = {'year': {'label': 'Year', 'file': '2000', 'discogs': '2001'}}
    result = prompt_tag_resolution(diffs)
    assert result['year'] == '2001'


def test_prompt_custom_value(monkeypatch):
    inputs = iter(['t', '1999'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    diffs = {'year': {'label': 'Year', 'file': '2000', 'discogs': '2001'}}
    result = prompt_tag_resolution(diffs)
    assert result['year'] == '1999'


def test_prompt_retries_on_invalid_input(monkeypatch):
    inputs = iter(['x', 'z', 'd'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    diffs = {'year': {'label': 'Year', 'file': '2000', 'discogs': '2001'}}
    result = prompt_tag_resolution(diffs)
    assert result['year'] == '2001'


def test_prompt_resolves_multiple_tags(monkeypatch):
    responses = iter(['f', 'd'])
    monkeypatch.setattr('builtins.input', lambda _: next(responses))
    diffs = {
        'year':  {'label': 'Year',  'file': '2000', 'discogs': '2001'},
        'genre': {'label': 'Genre', 'file': 'Electronic', 'discogs': 'House'},
    }
    result = prompt_tag_resolution(diffs)
    assert result['year'] == '2000'
    assert result['genre'] == 'House'


# --- apply_tags ---

@patch("plugins.compareAndEdit.ID3")
def test_apply_tags_saves_with_v2_and_removes_v1(mock_id3):
    mock_tags = MagicMock()
    mock_id3.return_value = mock_tags
    mock_mp3 = MagicMock()
    mock_mp3.path = "/tmp/test.mp3"
    apply_tags(mock_mp3, {'year': '2001'})
    mock_tags.save.assert_called_once_with("/tmp/test.mp3", v1=0, v2_version=3)


@patch("plugins.compareAndEdit.ID3")
def test_apply_tags_writes_correct_frames(mock_id3):
    mock_tags = MagicMock()
    mock_id3.return_value = mock_tags
    mock_mp3 = MagicMock()
    mock_mp3.path = "/tmp/test.mp3"
    apply_tags(mock_mp3, {'artist': 'Aerosmith', 'year': '1994'})
    set_keys = [c.args[0] for c in mock_tags.__setitem__.call_args_list]
    assert 'TPE1' in set_keys
    assert 'TDRC' in set_keys


@patch("plugins.compareAndEdit.ID3")
def test_apply_tags_creates_header_for_v1_only_file(mock_id3):
    from mutagen.id3 import ID3NoHeaderError
    mock_fallback = MagicMock()
    mock_id3.side_effect = [ID3NoHeaderError, mock_fallback]
    mock_mp3 = MagicMock()
    mock_mp3.path = "/tmp/test.mp3"
    # Should not raise even when no ID3 header exists
    apply_tags(mock_mp3, {})


@patch("plugins.compareAndEdit.ID3")
def test_apply_tags_empty_dict_still_saves(mock_id3):
    mock_tags = MagicMock()
    mock_id3.return_value = mock_tags
    mock_mp3 = MagicMock()
    mock_mp3.path = "/tmp/test.mp3"
    apply_tags(mock_mp3, {})
    mock_tags.save.assert_called_once()


# --- display_comparison ---

def test_display_comparison_runs_without_error(capsys):
    display_comparison("song.mp3", FILE_TAGS, DISCOGS_TAGS)
    out = capsys.readouterr().out
    assert "song.mp3" in out
    assert "DIFFERS" in out


def test_display_comparison_shows_matching_tags(capsys):
    display_comparison("song.mp3", FILE_TAGS, FILE_TAGS.copy())
    out = capsys.readouterr().out
    assert "DIFFERS" not in out
