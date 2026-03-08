#!/usr/bin/env python3
import pytest
from unittest.mock import MagicMock, patch
from context import __projectpath
from mp3_tagger import VERSION_1, VERSION_2, VERSION_BOTH
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

@patch("plugins.compareAndEdit.MP3File.set_version")
def test_apply_tags_uses_version2_for_id3v2_file(mock_set_version):
    mock_mp3 = MagicMock()
    mock_mp3.id3_version = '2.3'
    apply_tags(mock_mp3, {'year': '2001'})
    mock_set_version.assert_any_call(VERSION_2)


@patch("plugins.compareAndEdit.MP3File.set_version")
def test_apply_tags_uses_version1_for_id3v1_file(mock_set_version):
    mock_mp3 = MagicMock()
    mock_mp3.id3_version = '1.1'
    apply_tags(mock_mp3, {'year': '2001'})
    mock_set_version.assert_any_call(VERSION_1)


@patch("plugins.compareAndEdit.MP3File.set_version")
def test_apply_tags_restores_version_both_after_save(mock_set_version):
    mock_mp3 = MagicMock()
    mock_mp3.id3_version = '2.3'
    apply_tags(mock_mp3, {'year': '2001'})
    mock_set_version.assert_called_with(VERSION_BOTH)


@patch("plugins.compareAndEdit.MP3File.set_version")
def test_apply_tags_sets_attributes_and_saves(mock_set_version):
    mock_mp3 = MagicMock()
    mock_mp3.id3_version = '2.3'
    apply_tags(mock_mp3, {'year': '2001', 'genre': 'House'})
    assert mock_mp3.year == '2001'
    assert mock_mp3.genre == 'House'
    mock_mp3.save.assert_called_once()


@patch("plugins.compareAndEdit.MP3File.set_version")
def test_apply_tags_maps_genre_to_int_for_v1(mock_set_version):
    mock_mp3 = MagicMock()
    mock_mp3.id3_version = '1.1'
    apply_tags(mock_mp3, {'genre': 'Rock'})
    assert mock_mp3.genre == 17  # Rock is index 17 in ID3v1 GENRES


@patch("plugins.compareAndEdit.MP3File.set_version")
def test_apply_tags_skips_unknown_genre_for_v1(mock_set_version, capsys):
    mock_mp3 = MagicMock()
    mock_mp3.id3_version = '1.1'
    apply_tags(mock_mp3, {'genre': 'Synthwave'})
    out = capsys.readouterr().out
    assert 'Warning' in out
    mock_mp3.save.assert_called_once()  # still saves even if genre skipped


@patch("plugins.compareAndEdit.MP3File.set_version")
def test_apply_tags_empty_dict_still_saves(mock_set_version):
    mock_mp3 = MagicMock()
    mock_mp3.id3_version = '2.3'
    apply_tags(mock_mp3, {})
    mock_mp3.save.assert_called_once()


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
