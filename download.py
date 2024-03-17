#!/usr/bin/env python3

import argparse
import os
import shutil
import urllib.request
import zipfile
from config import *

def main():
    if not os.path.exists(SRC_DIR):
        os.makedirs(SRC_DIR)

    print("Download FiraCode")
    download_fira_code()

    print("Download IBM Plex Sans JP")
    download_plex_sans()

    print("Download NerdFont Patcher")
    download_font_patcher()


def download_fira_code():
    dl_path = '/tmp/FiraCode.zip'
    ttf_path = 'ttf/'
    # download
    urllib.request.urlretrieve(FRCD_URL, dl_path)
    with zipfile.ZipFile(dl_path) as zf:
        for weight in FRCD_WEIGHTS:
            outpath = SRC_DIR + '/' + FRCD_NAME.format(weight)
            basename = os.path.basename(outpath)
            # extract
            zf.extract(ttf_path + basename, '/tmp')
            # move
            shutil.move('/tmp/' + ttf_path + basename, outpath)


def download_plex_sans():
    dl_path = '/tmp/PlexSans.zip'
    ttf_path = 'IBM-Plex-Sans-JP/fonts/complete/ttf/hinted/'
    # download
    urllib.request.urlretrieve(PLEX_URL, dl_path)
    # extract
    with zipfile.ZipFile(dl_path) as zf:
        for weight in PLEX_WEIGHTS:
            outpath = SRC_DIR + '/' + PLEX_NAME.format(weight)
            basename = os.path.basename(outpath)
            # extract
            zf.extract(ttf_path + basename, '/tmp')
            # move
            shutil.move('/tmp/' + ttf_path + basename, outpath)


def download_font_patcher():
    # download
    path = '/tmp/FontPacher.zip'
    urllib.request.urlretrieve(NERD_URL, path)
    # extract
    with zipfile.ZipFile(path) as zf:
        zf.extractall(NERD_DIR)


if __name__ == '__main__':
    main()
