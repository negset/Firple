#!/usr/bin/env python3

import argparse
import math
import os
import shutil
import subprocess
import sys
from contextlib import redirect_stderr

import fontforge
import psMat
from fontTools.ttLib import TTFont

SRC_DIR = "./src"
OUT_DIR = "./out"
TMP_DIR = "./tmp"
SRC_FILES = {
    "Regular": [
        f"{SRC_DIR}/FiraCode-Regular.ttf",
        f"{SRC_DIR}/IBMPlexSansJP-Text.ttf",
        f"{SRC_DIR}/Firple-Italic.ttf",
    ],
    "Bold": [
        f"{SRC_DIR}/FiraCode-Bold.ttf",
        f"{SRC_DIR}/IBMPlexSansJP-Bold.ttf",
        f"{SRC_DIR}/Firple-BoldItalic.ttf",
    ],
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


stderr_target = sys.stderr


def main():
    global stderr_target
    parser = argparse.ArgumentParser(description=f"{FAMILY} Generator v{VERSION}")
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
    args = parser.parse_args()

    print(f"{FAMILY} Generator v{VERSION}")

    if args.suppress_err:
        stderr_target = open(os.devnull, "w", encoding="utf-8")

    # check if nerd fonts patcher exists
    if args.nerd and not files_exist([NERD_PATCHER]):
        print("Error: missing required files for nerd fonts patching", file=sys.stderr)
        return

    # create directories
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    if args.all or args.single is None:
        # generate all variants, weights and styles
        generate(slim=False, bold=False, italic=False, nerd=args.nerd)  # Regular
        generate(slim=False, bold=False, italic=True, nerd=args.nerd)  # Italic
        generate(slim=False, bold=True, italic=False, nerd=args.nerd)  # Bold
        generate(slim=False, bold=True, italic=True, nerd=args.nerd)  # Bold Italic
        generate(slim=True, bold=False, italic=False, nerd=args.nerd)  # Slim Regular
        generate(slim=True, bold=False, italic=True, nerd=args.nerd)  # Slim Italic
        generate(slim=True, bold=True, italic=False, nerd=args.nerd)  # Slim Bold
        generate(slim=True, bold=True, italic=True, nerd=args.nerd)  # Slim Bold Italic
    else:
        # generate a single font file with specified styles
        generate(
            slim="slim" in args.single,
            bold="bold" in args.single,
            italic="italic" in args.single,
            nerd=args.nerd,
        )

    # remove tmp directory
    if not args.keep_tmp_files and os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)


def files_exist(paths: list) -> bool:
    exist = True
    for path in paths:
        if not os.path.exists(path):
            print(f'Error: file not found: "{path}"', file=sys.stderr)
            exist = False
    return exist


def generate(slim: bool, bold: bool, italic: bool, nerd: bool) -> bool:
    family = f"{FAMILY} Slim" if slim else FAMILY
    weight = "Bold" if bold else "Regular"
    name = (
        family
        + (" " + weight if bold or not italic else "")
        + (" Italic" if italic else "")
    )
    name_without_space = (
        family.replace(" ", "")
        + "-"
        + (weight if bold or not italic else "")
        + ("Italic" if italic else "")
    )
    frcd_path = SRC_FILES[weight][0]
    plex_path = SRC_FILES[weight][1]
    ital_path = SRC_FILES[weight][2]
    out_path = f'{TMP_DIR}/{name_without_space.replace(FAMILY, "Tmp")}.ttf'

    # generation process
    print(f"\n[{name}]")
    if italic:
        upright_tmp_path = f'{TMP_DIR}/Tmp{"Slim" if slim else ""}-{weight}.ttf'
        if not os.path.exists(upright_tmp_path):
            # generate upright first
            ok = generate_upright(
                name, slim, weight, frcd_path, plex_path, upright_tmp_path
            )
            if not ok:
                return False
        # generate italic
        ok = generate_italic(name, slim, weight, upright_tmp_path, ital_path, out_path)
        if not ok:
            return False
    else:
        # generate upright
        ok = generate_upright(name, slim, weight, frcd_path, plex_path, out_path)
        if not ok:
            return False

    if nerd:
        print("Applying nerd fonts patch...")
        cmd = [
            "fontforge",
            "-quiet",
            "-script",
            NERD_PATCHER,
            out_path,
            "--quiet",
            "--complete",
            "--careful",
            "-out",
            TMP_DIR,
        ]
        with redirect_stderr(stderr_target):
            with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
                for line in proc.stdout:
                    print("  " + line.decode(), end="")
        if proc.returncode != 0:
            print(
                f'Error: patcher did not finish successfully for "{name}"',
                file=sys.stderr,
            )
            return False
        out_path = out_path.replace("-", "NerdFont-")

    print("Setting font parameters (1/2)...")
    with redirect_stderr(stderr_target):
        frpl = fontforge.open(out_path)
    frpl.familyname = family
    frpl.fontname = name_without_space
    frpl.fullname = name
    frpl.version = VERSION
    frpl.sfntRevision = float(VERSION)
    frpl.appendSFNTName("English (US)", "UniqueID", f"{VERSION};{name_without_space}")
    frpl.appendSFNTName("English (US)", "Version", f"Version {VERSION}")
    frpl.generate(out_path)
    frpl.close()

    print("Setting font parameters (2/2)...")
    frcd = TTFont(frcd_path)
    frpl = TTFont(out_path)
    w = frcd["OS/2"].xAvgCharWidth
    frpl["OS/2"].xAvgCharWidth = int(w * SLIM_SCALE) if slim else w
    frpl["post"].isFixedPitch = 1  # for macOS
    if italic:
        frpl["OS/2"].fsSelection &= ~(1 << 6)  # clear REGULAR bit
        frpl["OS/2"].fsSelection |= 1 << 0  # set ITALIC bit
        frpl["head"].macStyle |= 1 << 1  # set Italic bit
    out_path = f"{OUT_DIR}/{name_without_space}.ttf"
    frpl.save(out_path)
    frcd.close()
    frpl.close()

    print(f"Generation complete! (=> {out_path})")

    return True


def generate_upright(
    name: str, slim: bool, weight: str, frcd_path: str, plex_path: str, out_path: str
) -> bool:
    # check if src font files exist
    if not files_exist([frcd_path, plex_path]):
        print(f'Error: missing required files for "{name}"', file=sys.stderr)
        return False

    with redirect_stderr(stderr_target):
        frcd = fontforge.open(frcd_path)
        plex = fontforge.open(plex_path)
    w = frcd["A"].width
    half_width = int(w * SLIM_SCALE) if slim else w
    full_width = half_width * 2

    if slim:
        print("Condensing glyphs...")
        frcd.selection.all()
        frcd.transform(psMat.scale(SLIM_SCALE, 1))

    print("Copying glyphs...")
    plex.selection.none()
    frcd.selection.none()
    for i in range(sys.maxunicode + 1):
        if i in plex and not i in frcd or chr(i) in PLEX_PREFERRED_GLYPHS:
            plex.selection.select(("more",), i)
            frcd.selection.select(("more",), i)
        if chr(i) in PLEX_PREFERRED_GLYPHS:
            frcd[i].unlinkThisGlyph()
    plex.copy()
    frcd.paste()

    print("Transforming glyphs...")
    for glyph in frcd.selection.byGlyphs:
        scaled = glyph.width * PLEX_SCALE
        width = full_width if scaled > half_width else half_width
        offset = (width - scaled) / 2
        glyph.transform(
            psMat.compose(psMat.scale(PLEX_SCALE), psMat.translate(offset, 0))
        )
        glyph.width = width

    print("Generating temporary file...")
    frcd.fullname = name.replace(FAMILY, "Tmp")
    frcd.weight = weight
    frcd.copyright = f"{COPYRIGHT}\n{frcd.copyright}\n{plex.copyright}"
    frcd.os2_unicoderanges = tuple(
        a | b for a, b in zip(frcd.os2_unicoderanges, plex.os2_unicoderanges)
    )
    frcd.os2_codepages = tuple(
        a | b for a, b in zip(frcd.os2_codepages, plex.os2_codepages)
    )
    frcd.generate(out_path)
    frcd.close()
    plex.close()

    return True


def generate_italic(
    name: str, slim: bool, weight: str, frpl_path: str, ital_path: str, out_path: str
) -> bool:
    # check if src font files exist
    if not files_exist([frpl_path, ital_path]):
        print(f'Error: missing required files for "{name}"', file=sys.stderr)
        return False

    with redirect_stderr(stderr_target):
        frpl = fontforge.open(frpl_path)
        ital = fontforge.open(ital_path)

    if slim:
        print("Condensing glyphs...")
        ital.selection.all()
        ital.transform(
            psMat.compose(
                psMat.scale(SLIM_SCALE, 1),
                psMat.skew(
                    math.radians(ITALIC_SKEW)
                    - math.atan(math.tan(math.radians(ITALIC_SKEW)) * SLIM_SCALE)
                ),
            )
        )
        for glyph in ital.glyphs():
            glyph.width = int(glyph.width * SLIM_SCALE)

    print("Transforming glyphs...")
    frpl.selection.all()
    frpl.unlinkReferences()
    frpl.transform(
        psMat.compose(
            psMat.translate(ITALIC_OFFSET * SLIM_SCALE, 0),
            psMat.skew(math.radians(ITALIC_SKEW)),
        )
    )

    print("Copying glyphs...")
    # ital.selection.none()
    # frpl.selection.none()
    # for i in range(sys.maxunicode + 1):
    #     if i in ital and i in frpl:
    #         ital.selection.select(("more",), i)
    #         frpl.selection.select(("more",), i)
    # ital.copy()
    # frpl.paste()
    ital.selection.none()
    frpl.selection.none()
    for i in range(sys.maxunicode + 1):
        if i in ital and i in frpl:
            frpl.selection.select(("more",), i)
    frpl.clear()
    frpl.mergeFonts(ital)

    print("Generating temporary file...")
    frpl.fullname = name.replace(FAMILY, "Tmp")
    frpl.italicangle = -ITALIC_SKEW
    if not weight == "Regular":
        frpl.appendSFNTName("English (US)", "SubFamily", f"{weight} Italic")
    frpl.generate(out_path)
    frpl.close()
    ital.close()

    return True


if __name__ == "__main__":
    main()
