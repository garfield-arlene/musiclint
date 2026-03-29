#!/usr/bin/env python3
import os
import glob
from dotenv import load_dotenv
from plugins.cliArgs import cliArgs
from plugins.logIT import logIT

__version__ = '1.3.0'

load_dotenv()



def main():
    if args.database == 'discogs':
        print("Using Discogs.com for online DB\n")
    elif args.database == 'musicbrainz':
        print("Using MusicBrainz for online DB\n")

    process_mp3  = args.mp3  or args.all
    process_flac = args.flac or args.all

    if process_mp3:
        import plugins.processMp3

        if args.verbosity:
            logger.write("Library directory: " + args.library)
            logger.write("Processing mp3 files")

        plugins.processMp3.processMP3Files(args.library, args.verbosity, args.database)

    if process_flac:
        import plugins.processFlac

        if args.verbosity:
            logger.write("Library directory: " + args.library)
            logger.write("Processing flac files")

        plugins.processFlac.processFLACFiles(args.library, args.verbosity, args.database)


if __name__ == "__main__":
    args = cliArgs().args
    logger = logIT("musiclint.log")
    logger.write()
    main()


