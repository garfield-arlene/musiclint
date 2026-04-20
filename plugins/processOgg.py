#!/usr/bin/env python3

import logging
import os
import readline
import sys
from mutagen.oggvorbis import OggVorbis, OggVorbisHeaderError
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
)

# Mapping from internal tag names to Vorbis Comment field names
_OGG_TAG_MAP = {
    'song':   'title',
    'artist': 'artist',
    'album':  'album',
    'year':   'date',
    'track':  'tracknumber',
    'genre':  'genre',
}


def _input_with_default(prompt, default=''):
    '''Show an input prompt with a pre-filled editable default value.'''
    readline.set_startup_hook(lambda: readline.insert_text(default))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


def _get_file_tags(ogg):
    '''Read Vorbis Comment tags from a mutagen OggVorbis object into the internal tag dict.'''
    tags = {}
    for internal_key, vorbis_key in _OGG_TAG_MAP.items():
        vals = ogg.get(vorbis_key, [])
        tags[internal_key] = str(vals[0]).strip() if vals else ''
    return tags


def _display_file_tags(filename, file_tags):
    '''Display file tags when no database comparison is available.'''
    print(f"\n  Tags for: {filename}")
    for tag, val in file_tags.items():
        print(f"    {tag:<10}: {val or '(empty)'}")
    print()


def _apply_tags(filepath, resolved_tags):
    '''Write resolved tags back to the OGG file via mutagen.'''
    try:
        ogg = OggVorbis(filepath)
    except Exception as e:
        raise RuntimeError(f"Could not read tags from {filepath}: {e}") from e

    for internal_key, value in resolved_tags.items():
        vorbis_key = _OGG_TAG_MAP.get(internal_key)
        if vorbis_key:
            ogg[vorbis_key] = [value]

    try:
        ogg.save()
    except Exception as e:
        raise RuntimeError(f"Could not write tags to {filepath}: {e}") from e

    print("  Tags saved.\n")


def _read_tags(filepath):
    '''Read tags back from disk for post-save verification. Returns None on failure.'''
    try:
        ogg = OggVorbis(filepath)
    except Exception:
        return None
    tags = {}
    for internal_key, vorbis_key in _OGG_TAG_MAP.items():
        vals = ogg.get(vorbis_key, [])
        tags[internal_key] = str(vals[0]).strip() if vals else ''
    return tags


def processOGGFiles(libPath, verbosity, database):
    '''
    Walk libPath for .ogg files. For each file:
      - Read its Vorbis Comment tags.
      - If a database is specified, search for a matching release,
        display a side-by-side comparison, and prompt the user to resolve
        any differences (copy database value, keep file value, or type custom).
      - Write any chosen changes back to the file.
    '''
    ogg_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(libPath)
        for f in files
        if f.lower().endswith('.ogg')
    ]

    total = len(ogg_files)
    print(f"Found {total} ogg file(s).\n")

    if not ogg_files:
        return

    # Resolve database functions once up front
    if database == 'musicbrainz':
        _auth_fn         = authMusicBrainz
        _find_releases   = mb_find_releases
        _fetch_release   = mb_fetch_release
        _pick_release_fn = mb_pick_release
        db_label         = 'MusicBrainz'
        auth_msg         = 'Connecting to MusicBrainz...'
    else:
        _auth_fn         = authDiscogs
        _find_releases   = discogs_find_releases
        _fetch_release   = discogs_fetch_release
        _pick_release_fn = discogs_pick_release
        db_label         = 'Discogs'
        auth_msg         = 'Authenticating with Discogs...'

    auth_data = None

    for idx, filepath in enumerate(ogg_files, start=1):
        root     = os.path.dirname(filepath)
        filename = os.path.basename(filepath)

        if verbosity >= 2:
            logging.info(filepath)

        print(f"\n[{idx}/{total}] Processing: {filename}")

        try:
            ogg = OggVorbis(filepath)
            file_tags = _get_file_tags(ogg)
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

        # typical layout: Library/Artist/Album/track.ogg
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
                        _apply_tags(filepath, resolved)
                        saved = _read_tags(filepath)
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
