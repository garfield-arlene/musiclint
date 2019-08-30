#!/usr/bin/env python3.7
from context import __projectpath
from plugins.logIT import logIT

old = open(f"{__projectpath}/musiclint.log","r")
oldlog_file = len(old.readlines())
old.close()

logger = logIT(f"{__projectpath}/musiclint.log").write("test message from: test_logIT_logging_class.py ")


def test_if_log_is_written_to_with_new_lines():
    new = open(f"{__projectpath}/musiclint.log","r")
    newlog_file = len(new.readlines())
    new.close()
    assert oldlog_file < newlog_file


def main():
    test_if_log_is_written_to_with_new_lines()


if __name__ == "__main__":
    main()
