# musiclint
Search your music library, verify the meta tags, and suggest missing albums from artists already in your library

Linting
--------
Linting, as applied to programming, is the process of verifying syntax and style of your program code before compiling and running it. Here, I am verifying the tags so the next time you play you music, it will display the proper information.

Usage
-------
musiclint.py [-v] -l /path/to/directory

TESTS
------
pytest tests/test_*


TO DO:
* Take the found file,album, and band found from the filesystem and pass it to the OLMDB query
* Add verbosity to logging for changes and tags
* Add optional config file 
* Read config file if argument is not supplied
* Save supplied arguments to config file if not found in the config file