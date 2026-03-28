# musiclint v1.2.0
Search your music library, verify the meta tags, and suggest missing albums from artists already in your library

Linting
--------
Linting, as applied to programming, is the process of verifying syntax and style of your program code before compiling and running it. Here, I am verifying the tags so the next time you play your music, it will display the proper information.

Usage
-------
```
musiclint.py [-v] [-m] [-f] [-a] [-d discogs] -l /path/to/directory
```

Options:
- `-l`, `--library`   Path to the music library root directory
- `-m`, `--mp3`       Parse mp3 audio files and display/edit tags
- `-f`, `--flac`      Parse flac audio files and display/edit tags
- `-a`, `--all`       Parse all supported audio formats (mp3, flac)
- `-d`, `--database`  Online database to query (supported: `discogs`)
- `-v`, `--verbosity` Increase verbosity (repeat for more detail)
- `-V`, `--version`   Display the version

Tag Editing
-----------
When run with `-m -d discogs` or `-f -d discogs`, musiclint compares each file's existing tags against Discogs release data and lets you resolve any differences interactively. Changes are written back to the file using mutagen.

- **MP3**: tags are stored as ID3v2.3 frames. ID3v1-only files are upgraded automatically.
- **FLAC**: tags are stored as Vorbis Comments (title, artist, album, date, tracknumber, genre).

Dependencies
------------
Install required packages:
```
pip install -r requirements.txt
```

Key dependencies: `mp3-tagger`, `mutagen`, `oauth2`, `python-dotenv`

Set Discogs OAuth credentials in a `.env` file:
```
DISCOGS_CONSUMER_KEY=your_key
DISCOGS_CONSUMER_SECRET=your_secret
```

TESTS
------
```
pytest tests/test_*
```

TO DO:
* Take the found file, album, and band found from the filesystem and pass it to the OLMDB query
* Add verbosity to logging for changes and tags
* Add optional config file
* Read config file if argument is not supplied
* Save supplied arguments to config file if not found in the config file
