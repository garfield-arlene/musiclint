# musiclint Task List

## Critical

- [x] **#1 — Revoke and replace hardcoded OAuth credentials** (`queryDiscogs.py:27-28`)
  - Revoke the exposed `consumer_key` and `consumer_secret` on Discogs immediately
  - Move credentials to environment variables or a `.env` file
  - Add `.env` to `.gitignore`
  - Update `queryDiscogs.py` to read from `os.environ` instead

## High

- [x] **#2 — Remove stray undefined name** (`queryDiscogs.py:106`)
  - Delete the line `UjugggWWDj` which causes a `NameError` at runtime

- [x] **#3 — Fix `none` to `None`** (`queryDiscogs.py:135`)
  - Replace `if (at is none):` with `if (at is None):`

- [x] **#4 — Replace Python 2 `urllib.urlretrieve` and fix path traversal** (`queryDiscogs.py:182`)
  - Replace `urllib.urlretrieve` with `urllib.request.urlretrieve`
  - Sanitize the filename derived from the URL using `os.path.basename()` to prevent path traversal attacks

- [x] **#5 — Replace bare `except` clause** (`queryDiscogs.py:183`)
  - Replace bare `except:` with `except Exception as e:`
  - Include the error in the exit message for better debugging

## Medium

- [ ] **#6 — Add missing `logging` import** (`queryDiscogs.py:21`)
  - Add `import logging` at the top of `queryDiscogs.py`

- [ ] **#7 — Fix undefined variable scope between `authDiscogs` and `queryDiscogs`** (`queryDiscogs.py:130-147`)
  - Variables `at`, `ats`, `consumer`, and `user_agent` are defined in `authDiscogs()` but used in `queryDiscogs()` without being passed or returned
  - Refactor `authDiscogs()` to return these values
  - Update `queryDiscogs()` to accept them as parameters

- [ ] **#8 — Remove early `break` from file processing loop** (`processMp3.py:35`)
  - Remove the `break` statement that causes only one `.mp3` file per directory to be processed
