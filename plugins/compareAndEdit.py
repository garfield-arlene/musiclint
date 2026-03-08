#!/usr/bin/python3

from mp3_tagger import VERSION_2

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
    Switches to VERSION_2 (ID3v2) before writing to avoid TagSetError on
    tags that do not support simultaneous multi-version writes.
    '''
    mp3.version = VERSION_2
    for tag, value in resolved_tags.items():
        setattr(mp3, tag, value)
    mp3.save()
    print("  Tags saved.\n")
