#!/usr/bin/env python3

# Font Settings
FAMILY = 'FiraPlexNFsq'
VERSION = '1.00'
COPYRIGHT = 'Copyright 2024 tbando'
PLEX_SCALE = 1.9
PLEX_PREFERRED_GLYPHS = ['「', '」']
ITALIC_SKEW = 12
ITALIC_OFFSET = -100
SLIM_SCALE = 0.8

# Weights
WEIGHTS_MAP = {
#    FiraPlex     Firacode    IBM Plex
    'Light':    ['Light',    'Light'],
    'Regular':  ['Regular',  'Regular'],
    'Text':     ['Retina',   'Text'],
    'Medium':   ['Medium',   'Medium'],
    'SemiBold': ['SemiBold', 'SemiBold'],
    'Bold':     ['Bold',     'Bold'],
}
FRCD_WEIGHTS = [w[0] for w in WEIGHTS_MAP.values()]
PLEX_WEIGHTS = [w[1] for w in WEIGHTS_MAP.values()]

# Source version
FRCD_VER = '6.2'
PLEX_VER = '6.4.0'
NERD_VER = '3.1.1'

# Dir
SRC_DIR = './src'
NERD_DIR = './src/nerd-font-patcher'
DIST_DIR = './dist'
TMP_DIR = './tmp'

# Name
FRCD_NAME = 'FiraCode-{}.ttf'
PLEX_NAME = 'IBMPlexSansJP-{}.ttf'

# URL
FRCD_URL = 'https://github.com/tonsky/FiraCode/releases/download/'+ FRCD_VER + '/Fira_Code_v' + FRCD_VER +'.zip'
PLEX_URL = 'https://github.com/IBM/plex/releases/download/v'+ PLEX_VER + '/IBM-Plex-Sans-JP.zip'
NERD_URL = 'https://github.com/ryanoasis/nerd-fonts/releases/download/v' + NERD_VER + '/FontPatcher.zip'
