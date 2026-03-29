#!/usr/bin/env python3

from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TDRC, TRCK, TCON

_TAG_TO_FRAME = {
    'song':   TIT2,
    'artist': TPE1,
    'album':  TALB,
    'year':   TDRC,
    'track':  TRCK,
    'genre':  TCON,
}

# Tag keys as used by mp3_tagger, paired with display labels
TAGS = [
    ('song',   'Title'),
    ('artist', 'Artist'),
    ('album',  'Album'),
    ('year',   'Year'),
    ('track',  'Track'),
    ('genre',  'Genre'),
]

def display_comparison(filename, file_tags, discogs_tags, db_label='Online DB'):
    '''
    Print a side-by-side comparison table of file tags vs database tags.
    Rows with differing values are marked with *.
    Column widths adjust to fit the longest value in each column.
    '''
    rows = []
    for key, label in TAGS:
        f_val = str(file_tags.get(key, '') or '').strip()
        d_val = str(discogs_tags.get(key, '') or '').strip()
        rows.append((label, f_val, d_val, f_val != d_val))

    w_tag  = max(len('Tag'),      *(len(r[0]) for r in rows))
    w_file = max(len('File'),     *(len(r[1]) for r in rows))
    w_disc = max(len(db_label),   *(len(r[2]) for r in rows))
    total  = 2 + w_tag + 2 + w_file + 2 + w_disc

    border = '=' * total
    rule   = '  ' + '-' * w_tag + '  ' + '-' * w_file + '  ' + '-' * w_disc

    print(f'\n{border}')
    print(f'  File: {filename}')
    print(f'{border}')
    print(f'  {"Tag":<{w_tag}}  {"File":<{w_file}}  {db_label:<{w_disc}}')
    print(rule)
    for label, f_val, d_val, differs in rows:
        marker = '*' if differs else ' '
        print(f'{marker} {label:<{w_tag}}  {f_val:<{w_file}}  {d_val:<{w_disc}}')
    print(f'{border}\n')


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


def prompt_tag_resolution(differences, db_label='Online DB'):
    '''
    Interactively prompt the user to resolve each differing tag.
    Options: [f] keep file value, [d] use database value, [t] type custom.
    Returns a dict of {tag_key: chosen_value} for tags the user changed.
    '''
    if not differences:
        return {}

    print("  Resolve each differing tag:")
    print(f"  [f] Keep file value   [d] Use {db_label} value   [t] Type custom\n")

    resolved = {}
    for tag, vals in differences.items():
        label   = vals['label']
        f_val   = vals['file']    or '(empty)'
        d_val   = vals['discogs'] or '(empty)'

        print(f"  {label}:")
        print(f"    [f] File         : {f_val}")
        print(f"    [d] {db_label:<10}: {d_val}")
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


_FRAME_TO_TAG = {v.__name__: k for k, v in _TAG_TO_FRAME.items()}


def read_tags(filepath):
    '''
    Read ID3 tags from filepath using mutagen.
    Returns a dict matching the TAGS schema, or None if the file cannot be read.
    '''
    try:
        tags = ID3(filepath)
    except ID3NoHeaderError:
        return {k: '' for k, _ in TAGS}
    except Exception:
        return None
    return {
        tag_key: str(tags[frame_name]) if frame_name in tags else ''
        for frame_name, tag_key in _FRAME_TO_TAG.items()
    }


def apply_tags(filepath, resolved_tags):
    '''
    Write resolved tags to the file as ID3v2.3, removing any ID3v1 tags.
    Uses mutagen so that v1-only files are correctly upgraded to v2.
    Raises RuntimeError with a descriptive message if saving fails.
    '''
    try:
        tags = ID3(filepath)
    except ID3NoHeaderError:
        tags = ID3()
    except Exception as e:
        raise RuntimeError(f"Could not read tags from {filepath}: {e}") from e

    for tag, value in resolved_tags.items():
        frame_cls = _TAG_TO_FRAME.get(tag)
        if frame_cls:
            tags[frame_cls.__name__] = frame_cls(encoding=3, text=value)

    try:
        # v1=0 deletes any ID3v1 tag; v2_version=3 writes ID3v2.3
        tags.save(filepath, v1=0, v2_version=3)
    except Exception as e:
        raise RuntimeError(f"Could not write tags to {filepath}: {e}") from e

    print("  Tags saved.\n")
