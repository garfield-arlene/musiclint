#!/usr/bin/python3
import logging
import os
import glob

def findMP3Files(libPath):
    os.chdir(libPath)
    logging.info("Changing to directory: " + libPath)
    for file in glob.glob("*.mp3"):
        print(file)

