#!/usr/bin/python3

import argparse
import logging
import os
import glob
# from plugins.processMp3 import processMP3Files


parser = argparse.ArgumentParser()

def readable_dir(prospective_dir):
    '''
        Validate the specified path from the optional parameter
    '''
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if os.access(prospective_dir, os.R_OK):
        return prospective_dir
    else:
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))

parser.add_argument(
    '-l', '--library',
    type=readable_dir,
    # action="store_true",
    help="Specify the music library root directory",
)

parser.add_argument(
    '-v', '--verbosity',
    help="Increase verbosity",
    action="count",
    default=0,
)

parser.add_argument(
    '-V', '--version',
    help="Display the version of this script
    ",
)

parser.add_argument(
    '-m', '--mp3',
    help="Parse mp3 audio files",
    action="store_true",
)

args = parser.parse_args()



logging.basicConfig(filename='musiclint.log',level=logging.INFO,format='%(asctime)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info("******************** Start processing ********************")

if args.mp3:
    import plugins.processMp3

def main():
    if args.verbosity:
        logging.info("Library directory: " + args.library)
    
    if args.mp3:
        if args.verbosity:
            logging.info("Processing mp3 files")
        
        plugins.processMp3.processMP3Files(args.library, args.verbosity)


if __name__ == "__main__":
    main()


