#!/usr/bin/python3

from mp3_tagger import VERSION_1, VERSION_2, VERSION_BOTH, MP3File
from mp3_tagger.genres import GENRES

# Reverse lookup: genre string -> ID3v1 integer code
_GENRE_TO_INT = {v: k for k, v in GENRES.items()}

# Tag keys as used by mp3_tagger, paired with display labels
TAGS = [
    ('song',   'Title'),
    ('artist', 'Artist'),
    ('album',  'Album'),
    ('year',   'Year'),
    ('track',  'Track'),
    ('genre',  'Genre'),
]

_COL = 30  # column width for tag values


def display_comparison(filename, file_tags, discogs_tags):
    '''
    Print a side-by-side comparison table of file tags vs Discogs tags.
    Rows with differing values are flagged.
    '''
    print(f"\n{'=' * 74}")
    print(f"  File: {filename}")
    print(f"{'=' * 74}")
    print(f"  {'TAG':<10} {'FILE VALUE':<{_COL}} {'DISCOGS VALUE':<{_COL}}")
    print(f"  {'-' * 70}")
    for key, label in TAGS:
        f_val = file_tags.get(key, '') or ''
        d_val = discogs_tags.get(key, '') or ''
        flag = '  <-- DIFFERS' if f_val != d_val else ''
        print(f"  {label:<10} {f_val:<{_COL}} {d_val:<{_COL}}{flag}")
    print(f"{'=' * 74}\n")


def compare_tags(file_tags, discogs_tags):
    '''
    Return a dict of tags whose values differ between file and Discogs.
    Keys are tag names; values are dicts with 'label', 'file', 'discogs'.
    '''
    differences = {}
    for key, label in TAGS:
        f_val = str(file_tags.get(key, '') or '').strip()
        d_val = str(discogs_tags.get(key, '') or '').strip()
        if f_val != d_val:
            differences[key] = {'label': label, 'file': f_val, 'discogs': d_val}
    return differences


def prompt_tag_resolution(differences):
    '''
    Interactively prompt the user to resolve each differing tag.
    Options: [f] keep file value, [d] use Discogs value, [t] type custom.
    Returns a dict of {tag_key: chosen_value} for tags the user changed.
    '''
    if not differences:
        return {}

    print("  Resolve each differing tag:")
    print("  [f] Keep file value   [d] Use Discogs value   [t] Type custom\n")

    resolved = {}
    for tag, vals in differences.items():
        label   = vals['label']
        f_val   = vals['file']    or '(empty)'
        d_val   = vals['discogs'] or '(empty)'

        print(f"  {label}:")
        print(f"    [f] File   : {f_val}")
        print(f"    [d] Discogs: {d_val}")
        print(f"    [t] Custom")

        while True:
            choice = input("    Choice [f/d/t]: ").strip().lower()
            if choice == 'f':
                resolved[tag] = vals['file']
                break
            elif choice == 'd':
                resolved[tag] = vals['discogs']
                break
            elif choice == 't':
                resolved[tag] = input(f"    Enter value for {label}: ").strip()
                break
            else:
                print("    Invalid choice. Enter f, d, or t.")
        print()

    return resolved


def apply_tags(mp3, resolved_tags):
    '''
    Write resolved tag values back to the MP3File object and save to disk.

    Uses VERSION_1 for ID3v1-only files and VERSION_2 for files that already
    have an ID3v2 header. Restores VERSION_BOTH afterwards so subsequent reads
    in the same session are unaffected.

    For ID3v1 files, genre must be a standard integer-coded genre. If the
    chosen genre string is not in the ID3v1 genre list it is skipped with a
    warning rather than raising an error.
    '''
    is_v1_only = mp3.id3_version == '1.1'
    MP3File.set_version(VERSION_1 if is_v1_only else VERSION_2)

    skipped = []
    for tag, value in resolved_tags.items():
        if is_v1_only and tag == 'genre':
            genre_int = _GENRE_TO_INT.get(value)
            if genre_int is None:
                skipped.append(value)
                continue
            value = genre_int
        setattr(mp3, tag, value)

    mp3.save()
    MP3File.set_version(VERSION_BOTH)  # restore for subsequent reads

    for genre_val in skipped:
        print(f"  Warning: '{genre_val}' is not a standard ID3v1 genre — genre tag not saved.")
    print("  Tags saved.\n")
