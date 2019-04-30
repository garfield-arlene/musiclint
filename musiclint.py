#!/usr/bin/python3

import argparse
import logging
import os



parser = argparse.ArgumentParser()
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const", dest="loglevel", const=logging.DEBUG,
    default=logging.WARNING,
)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const", dest="loglevel", const=logging.INFO,
)

def readable_dir(prospective_dir):
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if os.access(prospective_dir, os.R_OK):
        return prospective_dir
    else:
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))

parser.add_argument(
    '-l', '--library',
    type=readable_dir,
    help="Specify the music library root directory",
)

args = parser.parse_args()

if args.library:
    print(args.library)

logging.basicConfig(filename='musiclint.log',level=logging.INFO,format='%(asctime)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info("Your music library starts in: " + args.library)

def main():
    print("hello")

if __name__ == "__main__":
    main()


