#!/usr/bin/env python3
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from context import __projectpath


# --- authDiscogs ---

def test_authDiscogs_exits_if_no_env_vars(monkeypatch):
    monkeypatch.delenv("DISCOGS_CONSUMER_KEY", raising=False)
    monkeypatch.delenv("DISCOGS_CONSUMER_SECRET", raising=False)
    from plugins.queryDiscogs import authDiscogs
    with pytest.raises(SystemExit):
        authDiscogs("/some/path", 0)


def test_authDiscogs_exits_if_key_missing(monkeypatch):
    monkeypatch.delenv("DISCOGS_CONSUMER_KEY", raising=False)
    monkeypatch.setenv("DISCOGS_CONSUMER_SECRET", "secret")
    from plugins.queryDiscogs import authDiscogs
    with pytest.raises(SystemExit):
        authDiscogs("/some/path", 0)


def test_authDiscogs_exits_if_secret_missing(monkeypatch):
    monkeypatch.setenv("DISCOGS_CONSUMER_KEY", "key")
    monkeypatch.delenv("DISCOGS_CONSUMER_SECRET", raising=False)
    from plugins.queryDiscogs import authDiscogs
    with pytest.raises(SystemExit):
        authDiscogs("/some/path", 0)


@patch("plugins.queryDiscogs.oauth")
def test_authDiscogs_returns_auth_tuple(mock_oauth, monkeypatch):
    monkeypatch.setenv("DISCOGS_CONSUMER_KEY", "test_key")
    monkeypatch.setenv("DISCOGS_CONSUMER_SECRET", "test_secret")

    mock_client = MagicMock()
    mock_resp = {"status": "200"}
    mock_content = b"oauth_token=tok&oauth_token_secret=toksec"
    mock_client.request.return_value = (mock_resp, mock_content)
    mock_oauth.Consumer.return_value = MagicMock()
    mock_oauth.Client.return_value = mock_client
    mock_oauth.Token.return_value = MagicMock()

    mock_access_content = b"oauth_token=acctok&oauth_token_secret=acctocsec"
    mock_client.request.side_effect = [
        (mock_resp, mock_content),        # request token call
        (mock_resp, mock_access_content), # access token call
    ]

    with patch("builtins.input", side_effect=["y", "verifier123"]):
        from plugins.queryDiscogs import authDiscogs
        result = authDiscogs("/some/path", 0)

    assert isinstance(result, tuple)
    assert len(result) == 4


@patch("plugins.queryDiscogs.oauth")
def test_authDiscogs_exits_on_bad_response(mock_oauth, monkeypatch):
    monkeypatch.setenv("DISCOGS_CONSUMER_KEY", "test_key")
    monkeypatch.setenv("DISCOGS_CONSUMER_SECRET", "test_secret")

    mock_client = MagicMock()
    mock_client.request.return_value = ({"status": "401"}, b"")
    mock_oauth.Consumer.return_value = MagicMock()
    mock_oauth.Client.return_value = mock_client

    from plugins.queryDiscogs import authDiscogs
    with pytest.raises(SystemExit):
        authDiscogs("/some/path", 0)


# --- queryDiscogs ---

@patch("plugins.queryDiscogs.authDiscogs")
@patch("plugins.queryDiscogs.oauth")
def test_queryDiscogs_calls_authDiscogs(mock_oauth, mock_auth, monkeypatch):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")

    mock_client = MagicMock()
    mock_resp = {"status": "200"}
    mock_releases = b'{"results": []}'
    mock_release_data = b'{"images": [{"uri": "https://example.com/img/cover.jpg"}]}'

    mock_client.request.side_effect = [
        (mock_resp, mock_releases),
        (mock_resp, mock_release_data),
    ]
    mock_oauth.Token.return_value = MagicMock()
    mock_oauth.Client.return_value = mock_client

    with patch("plugins.queryDiscogs.urllib.request.urlretrieve"):
        from plugins.queryDiscogs import queryDiscogs
        queryDiscogs("/some/path", 0)

    mock_auth.assert_called_once()


@patch("plugins.queryDiscogs.authDiscogs")
@patch("plugins.queryDiscogs.oauth")
def test_queryDiscogs_exits_on_bad_search_response(mock_oauth, mock_auth):
    mock_auth.return_value = ("at", "ats", MagicMock(), "agent/1.0")

    mock_client = MagicMock()
    mock_client.request.return_value = ({"status": "500"}, b"")
    mock_oauth.Token.return_value = MagicMock()
    mock_oauth.Client.return_value = mock_client

    from plugins.queryDiscogs import queryDiscogs
    with pytest.raises(SystemExit):
        queryDiscogs("/some/path", 0)
