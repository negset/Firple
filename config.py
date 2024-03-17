#!/usr/bin/env python3

# Font Settings
FAMILY = 'FiraPlexNFsq'
VERSION = '1.000'
COPYRIGHT = 'Copyright 2024 tbando'
PLEX_SCALE = 1.9
PLEX_PREFERRED_GLYPHS = ['「', '」']
ITALIC_SKEW = 12
ITALIC_OFFSET = -100
SLIM_SCALE = 0.8

# Dir
SRC_DIR = './src'
OUT_DIR = './out'
TMP_DIR = './tmp'


SRC_FILES = {
    'SemiBold': [
        SRC_DIR + '/FiraCode-SemiBold.ttf',
        SRC_DIR + '/IBMPlexSansJP-SemiBold.ttf',
    ]
}

FRCD_URL = 'https://github.com/tonsky/FiraCode/releases/latest/download/Fira_Code_v{}.zip'
PLEX_URL = 'https://github.com/IBM/plex/releases/latest/download/TrueType.zip'
NERD_URL = 'https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FontPatcher.zip'
NERD_PATCHER = './FontPatcher/font-patcher'

WEIGHTS = ["SemiBold"]
