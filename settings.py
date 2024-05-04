SRC_DIR = "./src"
OUT_DIR = "./out"
TMP_DIR = "./tmp"
SRC_FILES = {
    "Regular": [
        f"{SRC_DIR}/FiraCode-Regular.ttf",
        f"{SRC_DIR}/IBMPlexSansJP-Text.ttf",
    ],
    "Bold": [
        f"{SRC_DIR}/FiraCode-Bold.ttf",
        f"{SRC_DIR}/IBMPlexSansJP-Bold.ttf",
    ],
}
ITALIC_GLYPHS = ["a", "b", "e", "f", "g", "k", "q"]
ITALIC_FILES = {
    "Regular": {g: f"{SRC_DIR}/italic/Regular/{g}.svg" for g in ITALIC_GLYPHS},
    "Bold": {g: f"{SRC_DIR}/italic/Bold/{g}.svg" for g in ITALIC_GLYPHS},
}
NERD_PATCHER = "./FontPatcher/font-patcher"

FAMILY = "FirpleBeta"
VERSION = "5.000"
COPYRIGHT = "Copyright 2021 negset"
PLEX_SCALE = 1.9
PLEX_PREFERRED_GLYPHS = ["「", "」"]
ITALIC_SKEW = 12
ITALIC_OFFSET = -100
SLIM_SCALE = 0.8
