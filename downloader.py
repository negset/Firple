#!/usr/bin/env python3

import argparse
import os
import shutil
import urllib.request
import zipfile
from firple import SRC_FILES

FRCD_URL = 'https://github.com/tonsky/FiraCode/releases/latest/download/Fira_Code_v{}.zip'
PLEX_URL = 'https://github.com/IBM/plex/releases/latest/download/TrueType.zip'
NERD_URL = 'https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FontPatcher.zip'


def main():
    parser = argparse.ArgumentParser(
        description=f'File downloader for Firple Generator')
    parser.add_argument('-a', '--all', action='store_true',
                        help='download all files (default)')
    parser.add_argument('--fira-code', action='store_true',
                        help='download fira code')
    parser.add_argument('--plex-sans', action='store_true',
                        help='download plex sans')
    parser.add_argument('--font-patcher', action='store_true',
                        help='download nerd font patcher')
    args = parser.parse_args()

    if not (args.fira_code or args.plex_sans or args.font_patcher):
        args.all = True

    if args.all or args.fira_code:
        print("Fira Code...")
        fira_code()
    if args.all or args.plex_sans:
        print("Plex Sans...")
        plex_sans()
    if args.all or args.font_patcher:
        print("Font Patcher...")
        font_patcher()


def fira_code():
    # get version number
    with urllib.request.urlopen(FRCD_URL.rsplit('/', 2)[0]) as res:
        url = res.geturl()
    version = url.split('/')[-1]
    # download
    path = '/tmp/FiraCode.zip'
    urllib.request.urlretrieve(FRCD_URL.format(version), path)
    with zipfile.ZipFile(path) as zf:
        for weight in ['Regular', 'Bold']:
            outpath = SRC_FILES[weight][0]
            basename = os.path.basename(outpath)
            # extract
            zf.extract('ttf/' + basename, '/tmp')
            # move
            shutil.move('/tmp/ttf/' + basename, outpath)


def plex_sans():
    # download
    path = '/tmp/PlexSans.zip'
    urllib.request.urlretrieve(PLEX_URL, path)
    # extract
    with zipfile.ZipFile(path) as zf:
        for weight in ['Regular', 'Bold']:
            outpath = SRC_FILES[weight][1]
            basename = os.path.basename(outpath)
            # extract
            zf.extract('TrueType/IBM-Plex-Sans-JP/hinted/' + basename, '/tmp')
            # move
            shutil.move('/tmp/TrueType/IBM-Plex-Sans-JP/hinted/' + basename, outpath)


def font_patcher():
    # download
    path = '/tmp/FontPacher.zip'
    urllib.request.urlretrieve(NERD_URL, path)
    # extract
    with zipfile.ZipFile(path) as zf:
        zf.extractall('./FontPatcher')


if __name__ == '__main__':
    main()
