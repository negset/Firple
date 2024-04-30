#!/usr/bin/env python3

from argparse import ArgumentParser
from os.path import basename
from shutil import move
from tempfile import TemporaryDirectory
from urllib import request
from zipfile import ZipFile

from settings import SRC_FILES

FRCD_URL = (
    "https://github.com/tonsky/FiraCode/releases/latest/download/Fira_Code_v{}.zip"
)
PLEX_URL = "https://github.com/IBM/plex/releases/latest/download/TrueType.zip"
NERD_URL = (
    "https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FontPatcher.zip"
)


def main():
    parser = ArgumentParser(description="File downloader for Firple Generator")
    parser.add_argument(
        "-a", "--all", action="store_true", help="download all files (default)"
    )
    parser.add_argument("--fira-code", action="store_true", help="download fira code")
    parser.add_argument("--plex-sans", action="store_true", help="download plex sans")
    parser.add_argument(
        "--font-patcher", action="store_true", help="download nerd font patcher"
    )
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
    with request.urlopen(FRCD_URL.rsplit("/", 2)[0]) as res:
        url = res.geturl()
    version = url.split("/")[-1]
    with TemporaryDirectory() as tmpdir:
        # download
        path = f"{tmpdir}/FiraCode.zip"
        request.urlretrieve(FRCD_URL.format(version), path)
        # extract
        with ZipFile(path) as zf:
            for weight in ["Regular", "Bold"]:
                outpath = SRC_FILES[weight][0]
                name = basename(outpath)
                tmppath = zf.extract(f"ttf/{name}", tmpdir)
                move(tmppath, outpath)


def plex_sans():
    with TemporaryDirectory() as tmpdir:
        # download
        path = f"{tmpdir}/PlexSans.zip"
        request.urlretrieve(PLEX_URL, path)
        # extract
        with ZipFile(path) as zf:
            for weight in ["Regular", "Bold"]:
                outpath = SRC_FILES[weight][1]
                name = basename(outpath)
                tmppath = zf.extract(f"TrueType/IBM-Plex-Sans-JP/hinted/{name}", tmpdir)
                move(tmppath, outpath)


def font_patcher():
    with TemporaryDirectory() as tmpdir:
        # download
        path = f"{tmpdir}/FontPacher.zip"
        request.urlretrieve(NERD_URL, path)
        # extract
        with ZipFile(path) as zf:
            zf.extractall("./FontPatcher")


if __name__ == "__main__":
    main()
