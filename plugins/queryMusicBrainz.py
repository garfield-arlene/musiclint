#!/usr/bin/env python3

import musicbrainzngs

_APP_NAME    = 'musiclint'
_APP_VERSION = '1.0'
_APP_CONTACT = 'https://github.com/user/musiclint'


def authMusicBrainz(libPath, verbosity):
    '''
    Set up the MusicBrainz user-agent. No OAuth needed.
    Returns a tuple compatible with the (at, ats, consumer, user_agent) shape
    used by processMp3 / processFlac so no callers need changing.
    '''
    musicbrainzngs.set_useragent(_APP_NAME, _APP_VERSION, _APP_CONTACT)
    return (None, None, None, f'{_APP_NAME}/{_APP_VERSION}')


def _normalize_releases(release_list):
    '''Convert a MusicBrainz release-list into the Discogs-style results dict.'''
    normalized = []
    for r in release_list:
        artist_credit = r.get('artist-credit', [])
        artists = ', '.join(
            c['artist']['name']
            for c in artist_credit
            if isinstance(c, dict) and 'artist' in c
        )
        title = f"{artists} - {r['title']}" if artists else r['title']
        year  = r.get('date', '')[:4] if r.get('date') else ''
        normalized.append({
            'id':    r['id'],
            'title': title,
            'year':  year,
            'type':  'release',
        })
    return normalized


def _search_releases(params):
    '''Run a MusicBrainz release search and return a normalized results dict, or None.'''
    try:
        data = musicbrainzngs.search_releases(limit=5, **params)
    except musicbrainzngs.WebServiceError:
        return None
    releases = data.get('release-list', [])
    if not releases:
        return None
    return {'results': _normalize_releases(releases)}


def _search_by_recording(artist, track):
    '''
    Search MusicBrainz recordings for artist+track and return a normalized
    results dict built from the releases associated with the top hits, or None.
    '''
    try:
        data = musicbrainzngs.search_recordings(
            artist=artist, recording=track, limit=5
        )
    except musicbrainzngs.WebServiceError:
        return None

    seen = set()
    releases = []
    for rec in data.get('recording-list', []):
        for rel in rec.get('release-list', []):
            if rel['id'] not in seen:
                seen.add(rel['id'])
                releases.append(rel)

    if not releases:
        return None
    return {'results': _normalize_releases(releases[:5])}


def _album_name_matches(result_title, dir_album):
    '''Return True if dir_album appears (case-insensitively) in the result title.'''
    if not dir_album:
        return False
    album_part = result_title.split(' - ', 1)[-1] if ' - ' in result_title else result_title
    return dir_album.lower() in album_part.lower() or album_part.lower() in dir_album.lower()


def find_releases(artist, album, track, at, ats, consumer, user_agent,
                  dir_artist=None, dir_album=None):
    '''
    Search MusicBrainz using multiple fallback strategies.
    Parameters at, ats, consumer are accepted for interface compatibility
    with queryDiscogs but are unused.
    Returns (results, None, user_agent) or (None, None, None).

    Search priority:
      1. dir_artist + dir_album
      2. tag artist  + dir_album
      3. artist + album (tag)
      4. artist + track title (recording search)
      5. artist only
    '''
    strategies = []
    if dir_artist and dir_album:
        strategies.append(('release', {'artist': dir_artist, 'release': dir_album}))
    if artist and dir_album:
        strategies.append(('release', {'artist': artist, 'release': dir_album}))
    if artist and album:
        strategies.append(('release', {'artist': artist, 'release': album}))
    if artist and track:
        strategies.append(('recording', {'artist': artist, 'track': track}))
    if artist:
        strategies.append(('release', {'artist': artist}))

    for kind, params in strategies:
        if kind == 'recording':
            results = _search_by_recording(params['artist'], params['track'])
        else:
            results = _search_releases(params)
        if results:
            label = ', '.join(f'{k}={v}' for k, v in params.items())
            print(f"  MusicBrainz search: {label}")
            return results, None, user_agent

    return None, None, None


def fetch_release(client, user_agent, release_id, track):
    '''
    Fetch full release data from MusicBrainz and return a tag dict.
    client is accepted for interface compatibility but unused.
    Returns None on failure.
    '''
    try:
        data = musicbrainzngs.get_release_by_id(
            release_id,
            includes=['artists', 'recordings', 'tags', 'release-groups'],
        )
    except musicbrainzngs.WebServiceError:
        return None

    release = data.get('release', {})

    artist_credit = release.get('artist-credit', [])
    artists = ', '.join(
        c['artist']['name']
        for c in artist_credit
        if isinstance(c, dict) and 'artist' in c
    )

    # Prefer release tags, fall back to release-group tags
    tag_list = release.get('tag-list') or release.get('release-group', {}).get('tag-list', [])
    genre = ', '.join(
        t['name']
        for t in sorted(tag_list, key=lambda x: int(x.get('count', 0)), reverse=True)[:2]
    ) if tag_list else ''

    year = release.get('date', '')[:4] if release.get('date') else ''

    mb_tags = {
        'artist': artists,
        'album':  release.get('title', ''),
        'year':   year,
        'genre':  genre,
        'song':   '',
        'track':  '',
    }

    # Match the specific track across all media
    for medium in release.get('medium-list', []):
        for t in medium.get('track-list', []):
            recording = t.get('recording', {})
            title = recording.get('title') or t.get('title', '')
            if track and track.lower() in title.lower():
                mb_tags['song']  = title
                mb_tags['track'] = t.get('number') or t.get('position', '')
                break

    return mb_tags


def _pick_release(results, track=None, client=None, user_agent=None, dir_album=None):
    '''
    Show MusicBrainz results and let the user pick one.
    Interface is identical to the Discogs version in queryDiscogs.py.
    '''
    hits = results['results'][:5]

    track_flags = []
    if track:
        print("  Checking tracklists...", end='', flush=True)
        for r in hits:
            try:
                release_data = fetch_release(None, user_agent, r['id'], track)
                found = bool(release_data and release_data.get('song'))
            except Exception:
                found = False
            track_flags.append(found)
        print()
    else:
        track_flags = [None] * len(hits)

    album_flags = [
        _album_name_matches(r.get('title', ''), dir_album)
        for r in hits
    ]

    recommended = None
    for i, (tf, af) in enumerate(zip(track_flags, album_flags)):
        if tf and af:
            recommended = i
            break
    if recommended is None:
        for i, af in enumerate(album_flags):
            if af:
                recommended = i
                break
    if recommended is None:
        for i, tf in enumerate(track_flags):
            if tf:
                recommended = i
                break

    if recommended is None:
        print("\n  Warning: none of the results match the expected track or album directory.")
        print("  Consider using [m] to search with different terms.\n")

    print("\n  MusicBrainz results:")
    for i, (r, tf, af) in enumerate(zip(hits, track_flags, album_flags)):
        t_mark = 'T' if tf else ('-' if tf is False else ' ')
        a_mark = 'A' if af else ' '
        rec    = ' (recommended)' if i == recommended else ''
        print(f"    [{i+1}] [{t_mark}{a_mark}] {r.get('title', 'Unknown')} ({r.get('year', '?')}) — {r.get('type', '')}{rec}")
    print("         T=track found  A=album dir matches  -=not found")
    print(f"    [s] Skip / no match   [m] Manual search   [q] Quit")

    while True:
        choice = input("  Select result [1-{0}/s/m/q]: ".format(len(hits))).strip().lower()
        if choice == 's':
            return None
        if choice == 'm':
            return {'manual': True}
        if choice == 'q':
            return {'quit': True}
        if choice.isdigit() and 1 <= int(choice) <= len(hits):
            return hits[int(choice) - 1]
        print("  Invalid choice.")


def queryMusicBrainz(libPath, verbosity):
    '''Top-level entry point used by the plugin switcher.'''
    authMusicBrainz(libPath, verbosity)
