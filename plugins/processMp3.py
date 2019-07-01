#!/usr/bin/python3
import logging
import os
import glob
from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
from pprint import pprint
from re import escape

def processMP3Files(libPath, verbosity):
    '''
        Process mp3 files by finding files with the .mp3 extension
        and run the comparisons.
    '''
    if verbosity >= 2:
        logging.info("Found the following mp3 files")

    for root, directories, filenames in os.walk(libPath):
        for filename in filenames:
            if '.mp3' in filename:
                if verbosity >= 2:
                    logging.info(os.path.join(root,filename))
                
                # read mp3 tags
                print(filename)
                mp3 = MP3File(os.path.join(root,filename))
                # tags = mp3.get_tags()
                # pprint(tags)
                checkAlbum(mp3)
                exit()

                # search online music DB & pull tags
                # compaire DB tags & file tags

def checkAlbum(song):
    '''
        Compare the tag value with that of the value from the online DB search
    '''
    alb = song.album
    pprint(alb)
    print(alb[1])
    print("album: " + str(alb[1]).split(':')[1].split(')')[0])