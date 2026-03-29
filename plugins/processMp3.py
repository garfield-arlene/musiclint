#!/usr/bin/env python3

import logging
import os
import readline
import sys
from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
from plugins.queryDiscogs import (
    authDiscogs,
    find_releases as discogs_find_releases,
    fetch_release as discogs_fetch_release,
    _pick_release as discogs_pick_release,
)
from plugins.queryMusicBrainz import (
    authMusicBrainz,
    find_releases as mb_find_releases,
    fetch_release as mb_fetch_release,
    _pick_release as mb_pick_release,
)
from plugins.compareAndEdit import (
    display_comparison,
    compare_tags,
    prompt_tag_resolution,
    apply_tags,
    read_tags,
)

_TAG_NAMES = ['song', 'artist', 'album', 'year', 'track', 'genre']


def _input_with_default(prompt, default=''):
    '''Show an input prompt with a pre-filled editable default value.'''
    readline.set_startup_hook(lambda: readline.insert_text(default))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def _get_tag_value(mp3, tag_name):
    '''
    Safely extract a clean string value from an mp3_tagger property.
    mp3_tagger returns plain strings for v1-only files, and a list of
    ID3Tag objects (with a .value attribute) for files with v2 tags.
    Iterates v2-first so the most accurate tag wins.
    '''
    try:
        val = getattr(mp3, tag_name, None)
        if val is None:
            return ''
        if isinstance(val, (list, tuple)):
            for item in val:
                item_val = getattr(item, 'value', None)
                if item_val is not None:
                    return str(item_val).strip('\x00').strip()
            return ''
        return str(val).strip()
    except Exception:
        return ''


def _get_file_tags(mp3):
    '''Return a dict of all supported tag values from an MP3File object.'''
    return {tag: _get_tag_value(mp3, tag) for tag in _TAG_NAMES}


def _display_file_tags(filename, file_tags):
    '''Display file tags when no database comparison is available.'''
    print(f"\n  Tags for: {filename}")
    for tag, val in file_tags.items():
        print(f"    {tag:<10}: {val or '(empty)'}")
    print()


def processMP3Files(libPath, verbosity, database):
    '''
    Walk libPath for .mp3 files. For each file:
      - Read its ID3 tags.
      - If a database is specified, search Discogs for a matching release,
        display a side-by-side comparison, and prompt the user to resolve
        any differences (copy Discogs value, keep file value, or type custom).
      - Write any chosen changes back to the file.
    '''
    # Collect all mp3 files up front so we can show a total count.
    mp3_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(libPath)
        for f in files
        if f.endswith('.mp3')
    ]

    total = len(mp3_files)
    print(f"Found {total} mp3 file(s).\n")

    if not mp3_files:
        return

    # Resolve database functions once up front
    if database == 'musicbrainz':
        _auth_fn       = authMusicBrainz
        _find_releases = mb_find_releases
        _fetch_release = mb_fetch_release
        _pick_release_fn = mb_pick_release
        db_label       = 'MusicBrainz'
        auth_msg       = 'Connecting to MusicBrainz...'
    else:
        _auth_fn       = authDiscogs
        _find_releases = discogs_find_releases
        _fetch_release = discogs_fetch_release
        _pick_release_fn = discogs_pick_release
        db_label       = 'Discogs'
        auth_msg       = 'Authenticating with Discogs...'

    auth_data = None

    for idx, filepath in enumerate(mp3_files, start=1):
        root     = os.path.dirname(filepath)
        filename = os.path.basename(filepath)

        if verbosity >= 2:
            logging.info(filepath)

        print(f"\n[{idx}/{total}] Processing: {filename}")

        try:
            mp3 = MP3File(filepath)
            file_tags = _get_file_tags(mp3)
        except Exception as e:
            print(f"  Could not read file: {e}  Skipping.\n")
            continue

        if not database:
            _display_file_tags(filename, file_tags)
            continue

        # --- database path ---

        if auth_data is None:
            print(auth_msg)
            auth_data = _auth_fn(libPath, verbosity)

        at, ats, consumer, user_agent = auth_data

        # typical layout: Library/Artist/Album/track.mp3
        dir_album  = os.path.basename(root)
        dir_artist = os.path.basename(os.path.dirname(root))

        try:
            results, db_client, db_user_agent = _find_releases(
                file_tags.get('artist', ''),
                file_tags.get('album', ''),
                file_tags.get('song', ''),
                at, ats, consumer, user_agent,
                dir_artist=dir_artist,
                dir_album=dir_album,
            )
        except Exception as e:
            print(f"  {db_label} search failed: {e}  Skipping file.\n")
            continue

        if not results:
            print(f"  No {db_label} results found for this file.")
            _display_file_tags(filename, file_tags)
            continue

        while True:
            chosen = _pick_release_fn(
                results,
                track=file_tags.get('song', ''),
                client=db_client,
                user_agent=db_user_agent,
                dir_album=dir_album,
            )
            if not chosen:
                print("  Skipping file.\n")
                break

            if isinstance(chosen, dict) and chosen.get('quit'):
                print("  Quitting.\n")
                sys.exit(0)

            # Manual search: prompt for new terms and re-search
            if isinstance(chosen, dict) and chosen.get('manual'):
                default_track = file_tags.get('song', '') or os.path.splitext(filename)[0]
                m_artist = _input_with_default("  Search artist: ", file_tags.get('artist', '') or dir_artist).strip()
                m_album  = _input_with_default("  Search album:  ", file_tags.get('album', '')  or dir_album).strip()
                m_track  = _input_with_default("  Search track:  ", default_track).strip()
                try:
                    new_results, new_client, new_ua = _find_releases(
                        m_artist, m_album, m_track,
                        at, ats, consumer, user_agent,
                    )
                except Exception as e:
                    print(f"  Search failed: {e}\n")
                    continue
                if not new_results:
                    print("  No results found. Try different terms.\n")
                    continue
                results       = new_results
                db_client     = new_client
                db_user_agent = new_ua
                continue

            try:
                db_tags = _fetch_release(
                    db_client, db_user_agent, chosen['id'], file_tags.get('song', '')
                )
            except Exception as e:
                print(f"  Could not fetch release data: {e}  Try another.\n")
                continue

            if not db_tags:
                print("  Could not fetch release data. Try another.\n")
                continue

            display_comparison(filename, file_tags, db_tags, db_label)

            print("  [c] Continue resolving tags")
            print("  [r] Pick a different album")
            print("  [s] Skip this file")
            print("  [q] Quit")
            while True:
                action = input("  Choice [c/r/s/q]: ").strip().lower()
                if action in ('c', 'r', 's', 'q'):
                    break
                print("  Invalid choice. Enter c, r, s, or q.")

            if action == 'q':
                print("  Quitting.\n")
                sys.exit(0)
            if action == 's':
                print("  Skipping file.\n")
                break
            if action == 'r':
                continue

            # action == 'c': resolve and save
            differences = compare_tags(file_tags, db_tags)
            if differences:
                resolved = prompt_tag_resolution(differences, db_label)
                if resolved:
                    try:
                        apply_tags(filepath, resolved)
                        saved = read_tags(filepath)
                        if saved is not None:
                            print("  Tags now on disk:")
                            _display_file_tags(filename, saved)
                        else:
                            print("  Warning: could not read tags back from file.\n")
                    except RuntimeError as e:
                        print(f"  Error: {e}\n")
            else:
                print("  All tags match.\n")
            break

    logging.info("End\n")
