#!/usr/bin/env python3

import atexit
import math
import os
import shutil
import subprocess
import sys
from argparse import ArgumentParser
from contextlib import nullcontext

import fontforge
import psMat
from fontTools.ttLib import TTFont

from settings import *


def generate(slim: bool, bold: bool, italic: bool, nerd: bool, freeze_features: tuple):
    params = {}
    params["family"] = f"{FAMILY} Slim" if slim else FAMILY
    params["weight"] = "Bold" if bold else "Regular"
    params["name"] = (
        params["family"]
        + (" " + params["weight"] if bold or not italic else "")
        + (" Italic" if italic else "")
    )
    params["name_no_spaces"] = (
        params["family"].replace(" ", "")
        + "-"
        + (params["weight"] if bold or not italic else "")
        + ("Italic" if italic else "")
    )
    params["slim"] = slim
    params["italic"] = italic
    params["freeze_features"] = freeze_features if freeze_features else []

    print(f'\n[{params["name"]}]')
    path = generate_font(params)
    if nerd:
        path = apply_nerd_patch(path, params)
    path = set_font_params_1(path, params)
    path = set_font_params_2(path, params)
    print(f"Generation complete! (=> {path})")


def generate_font(params: dict) -> str:
    frcd_path = SRC_FILES[params["weight"]][0]
    plex_path = SRC_FILES[params["weight"]][1]
    out_path = f'{TMP_DIR}/{params["name_no_spaces"].replace(FAMILY, "Tmp")}.ttf'

    # check if src font files exist
    required(params["name"], [frcd_path, plex_path])

    if params["italic"]:
        glyph_paths = {
            c: f'{SRC_DIR}/italic/{params["weight"]}/{c}.svg' for c in ITALIC_CHARS
        }

        # check if glyph files exist
        required(params["name"], list(glyph_paths.values()))

        with ErrorSuppressor.suppress():
            frcd = fontforge.open(frcd_path)

        # unlink all reference
        frcd.selection.all()
        frcd.unlinkReferences()

        print("Importing italic glyphs...")
        for c in ITALIC_CHARS:
            frcd[c].clear()
            frcd[c].importOutlines(glyph_paths[c])
            frcd[c].width = frcd["A"].width
            frcd.selection.select(("less",), c)

        print("Skewing glyphs (1/2)...")
        # all glyphs except italic glyphs
        frcd.transform(
            psMat.compose(
                psMat.translate(ITALIC_OFFSET, 0),
                psMat.skew(math.radians(ITALIC_SKEW)),
            )
        )

        print("Hinting glyphs...")
        frcd.generate(out_path)
        frcd.close()
        cmd = [
            "ttfautohint",
            "--no-info",
            "--ignore-restrictions",
            out_path,
            f"{out_path}.hinted",
        ]
        cp = subprocess.run(cmd, check=False)
        if cp.returncode != 0:
            sys.exit(
                f'Error: ttfautohint did not finish successfully for "{params["name"]}"'
            )
        frcd_path = f"{out_path}.hinted"

    with ErrorSuppressor.suppress():
        frcd = fontforge.open(frcd_path)
        plex = fontforge.open(plex_path)

    if params["slim"]:
        print("Condensing glyphs...")
        frcd.selection.all()
        frcd.transform(psMat.scale(SLIM_SCALE, 1))
        if params["italic"]:
            # fix italic angle
            frcd.transform(
                psMat.skew(
                    math.atan((1 - SLIM_SCALE) * math.tan(math.radians(ITALIC_SKEW)))
                )
            )

    print("Copying glyphs...")
    plex.selection.none()
    frcd.selection.none()
    for i in range(sys.maxunicode + 1):
        is_plex_preferred = chr(i) in PLEX_PREFERRED_CHARS
        if is_plex_preferred or (i in plex and i not in frcd):
            plex.selection.select(("more",), i)
            frcd.selection.select(("more",), i)
        if is_plex_preferred:
            frcd[i].unlinkThisGlyph()
    plex.copy()
    frcd.paste()

    if "cv33" in params["freeze_features"]:
        freeze_feature("cv33", CV33_CHARS, frcd, plex, params)
    else:
        create_feature("cv33", CV33_CHARS, frcd, plex, params)

    if "ss11" in params["freeze_features"]:
        freeze_feature("ss11", SS11_CHARS, frcd, plex, params)
    else:
        create_feature("ss11", SS11_CHARS, frcd, plex, params)

    print("Transforming glyphs...")
    half_width = frcd["A"].width
    full_width = half_width * 2
    for glyph in frcd.selection.byGlyphs:
        scaled = glyph.width * PLEX_SCALE
        width = full_width if scaled > half_width else half_width
        offset = (width - scaled) / 2
        glyph.transform(
            psMat.compose(
                psMat.scale(PLEX_SCALE),
                psMat.translate(offset, 0),
            )
        )
        glyph.width = width

    if params["italic"]:
        print("Skewing glyphs (2/2)...")
        frcd.unlinkReferences()
        frcd.transform(
            psMat.compose(
                psMat.translate(ITALIC_OFFSET * SLIM_SCALE, 0),
                psMat.skew(math.radians(ITALIC_SKEW)),
            )
        )

    print("Generating temporary file...")
    frcd.fullname = params["name"].replace(FAMILY, "Tmp")
    frcd.weight = params["weight"]
    frcd.copyright = f"{COPYRIGHT}\n{frcd.copyright}\n{plex.copyright}"
    frcd.os2_unicoderanges = tuple(
        f | p for f, p in zip(frcd.os2_unicoderanges, plex.os2_unicoderanges)
    )
    frcd.os2_codepages = tuple(
        f | p for f, p in zip(frcd.os2_codepages, plex.os2_codepages)
    )
    if params["italic"]:
        frcd.italicangle = -ITALIC_SKEW
        if not params["weight"] == "Regular":
            frcd.appendSFNTName(
                "English (US)", "SubFamily", f'{params["weight"]} Italic'
            )
    frcd.generate(out_path)
    frcd.close()
    plex.close()

    return out_path


def create_feature(
    code: str,
    chars: list,
    frcd: fontforge.font,
    plex: fontforge.font,
    params: dict,
):
    print(f"Creating {code} feature...")
    glyph_paths = {
        c: f'{SRC_DIR}/{code}/{params["weight"]}/{c}.{code}.svg' for c in chars
    }
    # check if glyph files exist
    required(params["name"], list(glyph_paths.values()))

    lookup_name = f"{code} lookup"
    subtable_name = f"{code} lookup subtable"
    feature_script_lang = (
        (
            code,
            (
                ("DFLT", ("dflt",)),
                ("cyrl", ("dflt",)),
                ("grek", ("dflt",)),
                (
                    "latn",
                    (
                        "AFK ",
                        "AZE ",
                        "CAT ",
                        "CRT ",
                        "KAZ ",
                        "MOL ",
                        "PLK ",
                        "ROM ",
                        "TAT ",
                        "TRK ",
                        "dflt",
                    ),
                ),
                ("zinh", ("dflt",)),
                ("zyyy", ("dflt",)),
            ),
        ),
    )
    frcd.addLookup(lookup_name, "gsub_single", None, feature_script_lang)
    frcd.addLookupSubtable(lookup_name, subtable_name)

    for c in chars:
        g = frcd.createChar(-1, f"{c}.{code}")
        g.importOutlines(
            f'{SRC_DIR}/{code}/{params["weight"]}/{c}.{code}.svg',
            scale=False,
        )
        g.width = frcd[c].width
        g.transform(psMat.translate(0, plex.ascent - frcd.ascent))  # fix y gap
        frcd.selection.select(("more",), g)
        frcd[c].addPosSub(subtable_name, f"{c}.{code}")


def freeze_feature(
    code: str,
    chars: list,
    frcd: fontforge.font,
    plex: fontforge.font,
    params: dict,
):
    print(f"Freezing {code} feature...")
    glyph_paths = {
        c: f'{SRC_DIR}/{code}/{params["weight"]}/{c}.{code}.svg' for c in chars
    }
    # check if glyph files exist
    required(params["name"], list(glyph_paths.values()))

    for c in chars:
        w = frcd[c].width
        frcd[c].clear()
        frcd[c].importOutlines(
            f'{SRC_DIR}/{code}/{params["weight"]}/{c}.{code}.svg',
            scale=False,
        )
        frcd[c].transform(psMat.translate(0, plex.ascent - frcd.ascent))  # fix y gap
        frcd[c].width = w


def apply_nerd_patch(path: str, params: dict) -> str:
    # check if nerd fonts patcher exists
    required("nerd fonts patching", [NERD_PATCHER])

    print("Applying nerd fonts patch...")
    cmd = [
        "fontforge",
        "-quiet",
        "-script",
        NERD_PATCHER,
        path,
        "--quiet",
        "--complete",
        "--careful",
        "-out",
        TMP_DIR,
    ]
    with ErrorSuppressor.suppress():
        with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
            for line in proc.stdout:
                print("| " + line.decode(), end="")
    if proc.returncode != 0:
        sys.exit(f'Error: patcher did not finish successfully for "{params["name"]}"')
    return path.replace("-", "NerdFont-")


def set_font_params_1(path: str, params: dict) -> dict:
    print("Setting font parameters (1/2)...")
    with ErrorSuppressor.suppress():
        frpl = fontforge.open(path)
    frpl.familyname = params["family"]
    frpl.fontname = params["name_no_spaces"]
    frpl.fullname = params["name"]
    frpl.version = VERSION
    frpl.sfntRevision = float(VERSION)
    frpl.appendSFNTName(
        "English (US)", "UniqueID", f'{VERSION};{params["name_no_spaces"]}'
    )
    frpl.appendSFNTName("English (US)", "Version", f"Version {VERSION}")
    frpl.generate(path)
    frpl.close()
    return path


def set_font_params_2(path: str, params: dict) -> str:
    print("Setting font parameters (2/2)...")
    frcd = TTFont(SRC_FILES[params["weight"]][0])
    frpl = TTFont(path)
    w = frcd["OS/2"].xAvgCharWidth
    frpl["OS/2"].xAvgCharWidth = int(w * SLIM_SCALE) if params["slim"] else w
    frpl["post"].isFixedPitch = 1  # for macOS
    if params["italic"]:
        frpl["OS/2"].fsSelection &= ~(1 << 6)  # clear REGULAR bit
        frpl["OS/2"].fsSelection |= 1 << 0  # set ITALIC bit
        frpl["head"].macStyle |= 1 << 1  # set Italic bit
    out_path = f'{OUT_DIR}/{params["name_no_spaces"]}.ttf'
    frpl.save(out_path)
    frcd.close()
    frpl.close()
    return out_path


class ErrorSuppressor:
    enable = False

    def __init__(self):
        # copy stderr
        self.stderr_copy = os.dup(2)

    def __enter__(self):
        # replace stderr with null device
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
        os.close(devnull)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # restore stderr
        os.dup2(self.stderr_copy, 2)

    @classmethod
    def suppress(cls):
        return cls() if cls.enable else nullcontext()


def parse_arguments():
    parser = ArgumentParser(description=f"{FAMILY} Generator v{VERSION}")
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="generate all variants, weights and styles (default)",
    )
    parser.add_argument(
        "-s",
        "--single",
        choices=["slim", "bold", "italic"],
        nargs="*",
        help="generate a single font file as specified; ignored if -a is set",
    )
    parser.add_argument(
        "--disable-nerd-fonts",
        dest="nerd",
        action="store_false",
        help="disable nerd fonts patching",
    )
    parser.add_argument(
        "--freeze-features",
        choices=["cv33", "ss11"],
        nargs="*",
        help="freeze specified OpenType features",
    )
    parser.add_argument(
        "--keep-tmp-files",
        action="store_true",
        help="do not delete temporary files on exit",
    )
    parser.add_argument(
        "--show-fontforge-error",
        dest="suppress_error",
        action="store_false",
        help="show fontforge error messages",
    )
    return parser.parse_args()


def required(obj: str, paths: list) -> None:
    ok = True
    for path in paths:
        if not os.path.exists(path):
            print(f'file not found: "{path}"', file=sys.stderr)
            ok = False
    if not ok:
        sys.exit(f'Error: missing required files for "{obj}"')


def cleanup(keep_tmp_files: bool):
    # remove tmp directory
    if not keep_tmp_files and os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)


if __name__ == "__main__":
    print(f"{FAMILY} v{VERSION}")

    args = parse_arguments()

    # set ErrorSuppressor
    ErrorSuppressor.enable = args.suppress_error

    # create directories
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)

    # call cleanup on exit
    atexit.register(cleanup, args.keep_tmp_files)

    if args.all or args.single is None:
        # generate all variants, weights and styles
        # Regular
        generate(False, False, False, args.nerd, args.freeze_features)
        # Italic
        generate(False, False, True, args.nerd, args.freeze_features)
        # Bold
        generate(False, True, False, args.nerd, args.freeze_features)
        # Bold Italic
        generate(False, True, True, args.nerd, args.freeze_features)
        # Slim Regular
        generate(True, False, False, args.nerd, args.freeze_features)
        # Slim Italic
        generate(True, False, True, args.nerd, args.freeze_features)
        # Slim Bold
        generate(True, True, False, args.nerd, args.freeze_features)
        # Slim Bold Italic
        generate(True, True, True, args.nerd, args.freeze_features)
    else:
        # generate a single font file with specified styles
        generate(
            "slim" in args.single,
            "bold" in args.single,
            "italic" in args.single,
            args.nerd,
            args.freeze_features,
        )
