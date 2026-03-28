#!/usr/bin/env python3
import os
import glob
from dotenv import load_dotenv
from plugins.cliArgs import cliArgs
from plugins.logIT import logIT

__version__ = '1.1.0'

load_dotenv()



def main():
    if args.database:
        print("Using Discogs.com for online DB\n")
        import plugins.queryDiscogs

    if args.mp3:
        import plugins.processMp3

        if args.verbosity:
            logger.write("Library directory: " + args.library)

        if args.mp3:
            if args.verbosity:
                logger.write("Processing mp3 files")

            plugins.processMp3.processMP3Files(args.library, args.verbosity, args.database)


if __name__ == "__main__":
    args = cliArgs().args
    logger = logIT("musiclint.log")
    logger.write()
    main()


