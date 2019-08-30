#!/usr/bin/env python3.7
import argparse

class cliArgs:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            '-l', '--library',
            type=self.readable_dir,
            # action="store_true",
            help="Specify the music library root directory",
        )

        self.parser.add_argument(
            '-v', '--verbosity',
            help="Increase verbosity",
            action="count",
            default=0,
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

    @property
    def args(self):
        args = self.parser.parse_args()
        return args
