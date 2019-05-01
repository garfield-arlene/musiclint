#!/usr/bin/python3
import logging
import os
import glob

def findMP3Files(libPath, verbosity):
    if verbosity >= 2:
        logging.info("Found the following mp3 files")

    for root, directories, filenames in os.walk(libPath):
        for filename in filenames:
            if '.mp3' in filename:
                if verbosity >= 2:
                    logging.info(os.path.join(root,filename))

