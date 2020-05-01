#!/usr/bin/env python3.7
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
            help="Specify the music library root directory",
        )

        self.parser.add_argument(
            '-V', '--version',
            help="Display the version of this script",
        )

        self.parser.add_argument(
            '-m', '--mp3',
            help="Parse mp3 audio files",
            action="store_true",
        )

    def readable_dir(self,prospective_dir):
        '''
            Validate the specified path from the optional parameter
        '''
        if not os.path.isdir(prospective_dir):
            raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            return prospective_dir
        else:
            raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))

    def usableDB(self,prospective_db):
        '''
            Validate the specified online DB providor from the optional parameter
        '''
        validDBList = ['discogs']
        if prospective_db in validDBList:
            return prospective_db
        else:
            raise Exception("usableDB:{0} is not a valid DB".format(prospective_db))


    @property
    def args(self):
        args = self.parser.parse_args()
        return args
