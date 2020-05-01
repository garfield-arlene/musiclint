#!/usr/bin/python3

import logging
import os
import glob
from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
from pprint import pprint
from re import escape
from plugins.plugins import chooseDBPlugin

def processMP3Files(libPath, verbosity, database):
    '''
        Process mp3 files by finding files with the .mp3 extension
        and run the comparisons.
    '''
    if verbosity >= 2:
        logging.info("Found the following mp3 files")

    myPlugin = chooseDBPlugin(database)
    for root, directories, filenames in os.walk(libPath):
        for filename in filenames:
            if '.mp3' in filename:
                if verbosity >= 2:
                    logging.info(os.path.join(root,filename))
                    # logging.info("Database selected to query: " + database )
                
                
                # read mp3 tags
                print(filename)
                mp3 = MP3File(os.path.join(root,filename))
                checkAlbum(mp3)
                print('\n')

                
                break

                # search online music DB & pull tags
                # compaire DB tags & file tags
    logging.info("End\n")


def checkAlbum(song):
    '''
        Compare the tag value with that of the value from the online DB search
    '''
    alb = song.album
    pprint(alb)
    print(alb[1])
    print("album: " + str(alb[1]).split(':')[1].split(')')[0])