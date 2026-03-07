#!/usr/bin/env python3
import logging
import os
import tempfile
import pytest
from context import __projectpath
from plugins.logIT import logIT


@pytest.fixture
def log_file():
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
        path = f.name
    yield path
    # Reset root logger handlers so basicConfig works fresh in each test
    logging.root.handlers = []
    os.remove(path)


def test_write_creates_log_file(log_file):
    logger = logIT(log_file)
    logger.write("hello")
    assert os.path.exists(log_file)


def test_write_default_message_logs_start_marker(log_file):
    logger = logIT(log_file)
    logger.write()
    with open(log_file) as f:
        content = f.read()
    assert "Start processing" in content


def test_write_custom_message(log_file):
    logger = logIT(log_file)
    logger.write("test message")
    with open(log_file) as f:
        content = f.read()
    assert "test message" in content


def test_write_appends_multiple_messages(log_file):
    logger = logIT(log_file)
    logger.write("first")
    logging.root.handlers = []
    logger2 = logIT(log_file)
    logger2.write("second")
    with open(log_file) as f:
        lines = f.readlines()
    assert len(lines) >= 2


def test_write_converts_non_string_message(log_file):
    logger = logIT(log_file)
    logger.write(42)
    with open(log_file) as f:
        content = f.read()
    assert "42" in content


def test_log_location_stored(log_file):
    logger = logIT(log_file)
    assert logger.log_location == log_file
