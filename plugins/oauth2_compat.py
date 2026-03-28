#!/usr/bin/env python3
"""
Minimal oauth2-compatible shim backed by requests + requests-oauthlib.

Provides Consumer, Token, and Client with the same interface used by the
original oauth2 package so that existing code requires only a one-line
import change.
"""
import requests
from requests_oauthlib import OAuth1


class Consumer:
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret


class Token:
    def __init__(self, key=None, secret=None):
        self.key = key
        self.secret = secret
        self.verifier = None

    def set_verifier(self, verifier):
        self.verifier = verifier


class _Response:
    """Mimics the oauth2 response dict: resp['status'] returns a string."""
    def __init__(self, status_code):
        self._status = str(status_code)

    def __getitem__(self, key):
        if key == 'status':
            return self._status
        raise KeyError(key)

    def get(self, key, default=None):
        return self._status if key == 'status' else default


class Client:
    def __init__(self, consumer, token=None):
        self.consumer = consumer
        self.token = token

    def request(self, url, method='GET', headers=None):
        auth_kwargs = {
            'client_key': self.consumer.key,
            'client_secret': self.consumer.secret,
        }
        if self.token:
            auth_kwargs['resource_owner_key'] = self.token.key
            auth_kwargs['resource_owner_secret'] = self.token.secret
            if self.token.verifier:
                auth_kwargs['verifier'] = self.token.verifier

        auth = OAuth1(**auth_kwargs)
        method = method.upper()
        req_headers = headers or {}

        if method == 'POST':
            resp = requests.post(url, auth=auth, headers=req_headers)
        else:
            resp = requests.get(url, auth=auth, headers=req_headers)

        return _Response(resp.status_code), resp.content
