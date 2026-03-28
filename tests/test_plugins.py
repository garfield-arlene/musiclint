#!/usr/bin/env python3
import pytest
from context import __projectpath
from plugins.plugins import chooseDBPlugin, queryMusicBrainz


def test_chooseDBPlugin_discogs_returns_callable():
    result = chooseDBPlugin("discogs")
    assert callable(result)


def test_chooseDBPlugin_musicbrainz_returns_callable():
    result = chooseDBPlugin("musicbrainz")
    assert callable(result)


def test_chooseDBPlugin_discogs_returns_queryDiscogs_function():
    from plugins.queryDiscogs import queryDiscogs
    result = chooseDBPlugin("discogs")
    assert result is queryDiscogs


def test_chooseDBPlugin_musicbrainz_returns_queryMusicBrainz_function():
    result = chooseDBPlugin("musicbrainz")
    assert result is queryMusicBrainz


def test_chooseDBPlugin_invalid_returns_lambda():
    result = chooseDBPlugin("invalid_plugin")
    assert callable(result)
    assert result() == "Invalid plugin"


def test_chooseDBPlugin_empty_string_returns_lambda():
    result = chooseDBPlugin("")
    assert callable(result)
    assert result() == "Invalid plugin"


def test_queryMusicBrainz_returns_string():
    assert queryMusicBrainz() == "musicbrainz"
