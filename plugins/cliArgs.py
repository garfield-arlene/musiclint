#!/usr/bin/env python3
import os
import argparse

class cliArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            '-l', '--library',
            type=self.readable_dir,
            help="Specify the music library root directory",
        )

        self.parser.add_argument(
            '-v', '--verbosity',
            help="Increase verbosity",
            action="count",
            default=0,
        )

        self.parser.add_argument(
            '-d', '--database',
            type=self.usableDB,
            default='musicbrainz',
            help="Online database to use for tag lookup (default: musicbrainz)",
        )

        self.parser.add_argument(
            '-V', '--version',
            action='version',
            version='%(prog)s 1.3.0',
        )

        self.parser.add_argument(
            '-m', '--mp3',
            help="Parse mp3 audio files",
            action="store_true",
        )

        self.parser.add_argument(
            '-f', '--flac',
            help="Parse flac audio files",
            action="store_true",
        )

        self.parser.add_argument(
            '-a', '--all',
            help="Parse all supported audio file formats (mp3, flac)",
            action="store_true",
        )

    def readable_dir(self, prospective_dir):
        '''
            Validate the specified path from the optional parameter
        '''
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            return prospective_dir
        else:
            raise argparse.ArgumentTypeError("{0} is not a readable directory".format(prospective_dir))

    def usableDB(self, prospective_db):
        '''
            Validate the specified online DB provider from the optional parameter
        '''
        validDBList = ['discogs', 'musicbrainz']
        if prospective_db in validDBList:
            return prospective_db
        else:
            raise argparse.ArgumentTypeError(
                "'{0}' is not a supported database. Valid options: {1}".format(
                    prospective_db, ', '.join(validDBList)
                )
            )


    @property
    def args(self):
        args = self.parser.parse_args()
        return args
