SRC_DIR = "./src"
OUT_DIR = "./out"
TMP_DIR = "./tmp"
SRC_FILES = {
    "Regular": [
        f"{SRC_DIR}/FiraCode-Regular.ttf",
        f"{SRC_DIR}/IBMPlexSansJP-Regular.ttf",
    ],
    "Bold": [
        f"{SRC_DIR}/FiraCode-Bold.ttf",
        f"{SRC_DIR}/IBMPlexSansJP-Bold.ttf",
    ],
}
NERD_PATCHER = "./FontPatcher/font-patcher"

PLEX_PREFERRED_CHARS = ["「", "」"]
ITALIC_CHARS = [
    "a",
    "b",
    "e",
    "f",
    "g",
    "k",
    "q",
]
FEATURE_CHARS = {
    "cv33": ["uni3000"],
    "ss11": [
        "uni3071",
        "uni3074",
        "uni3077",
        "uni307A",
        "uni307D",
        "uni309C",
        "uni30D1",
        "uni30D4",
        "uni30D7",
        "uni30DA",
        "uni30DD",
        "uniFF9F",
    ],
}

FAMILY = "Firple"
VERSION = "5.100"
COPYRIGHT = "Copyright 2021 negset"
PLEX_SCALE = 2.0
ITALIC_SKEW = 12
ITALIC_OFFSET = -100
SLIM_SCALE = 0.85
