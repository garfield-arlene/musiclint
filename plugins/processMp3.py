#!/usr/bin/python3

import logging
import os
from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
from plugins.plugins import chooseDBPlugin
from plugins.queryDiscogs import authDiscogs, search_track
from plugins.compareAndEdit import (
    display_comparison,
    compare_tags,
    prompt_tag_resolution,
    apply_tags,
)

_TAG_NAMES = ['song', 'artist', 'album', 'year', 'track', 'genre']


def _get_tag_value(mp3, tag_name):
    '''
    Safely extract a clean string value from an mp3_tagger property.
    Handles both plain strings and list/tuple returns (VERSION_BOTH).
    '''
    try:
        val = getattr(mp3, tag_name, None)
        if val is None:
            return ''
        if isinstance(val, (list, tuple)):
            for item in reversed(val):
                if item is not None:
                    return str(item).strip()
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
    if verbosity >= 2:
        logging.info("Found the following mp3 files")

    auth_data = None

    for root, directories, filenames in os.walk(libPath):
        for filename in filenames:
            if not filename.endswith('.mp3'):
                continue

            filepath = os.path.join(root, filename)
            if verbosity >= 2:
                logging.info(filepath)

            print(f"\nProcessing: {filename}")
            mp3 = MP3File(filepath)
            file_tags = _get_file_tags(mp3)

            if database:
                # Authenticate once for the whole session
                if auth_data is None:
                    print("Authenticating with Discogs...")
                    auth_data = authDiscogs(libPath, verbosity)

                at, ats, consumer, user_agent = auth_data
                discogs_tags = search_track(
                    file_tags.get('artist', ''),
                    file_tags.get('album', ''),
                    file_tags.get('song', ''),
                    at, ats, consumer, user_agent,
                )

                if discogs_tags:
                    display_comparison(filename, file_tags, discogs_tags)
                    differences = compare_tags(file_tags, discogs_tags)
                    if differences:
                        resolved = prompt_tag_resolution(differences)
                        if resolved:
                            apply_tags(mp3, resolved)
                    else:
                        print("  All tags match.\n")
                else:
                    print("  No Discogs results found for this file.")
                    _display_file_tags(filename, file_tags)
            else:
                _display_file_tags(filename, file_tags)

    logging.info("End\n")
