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


class Firple:
    def generate(self, slim: bool, bold: bool, italic: bool, nerd: bool):
        # check if nerd fonts patcher exists
        if nerd:
            required("nerd fonts patching", [NERD_PATCHER])

        family = f"{FAMILY} Slim" if slim else FAMILY
        weight = "Bold" if bold else "Regular"
        name = (
            family
            + (" " + weight if bold or not italic else "")
            + (" Italic" if italic else "")
        )
        name_no_spaces = (
            family.replace(" ", "")
            + "-"
            + (weight if bold or not italic else "")
            + ("Italic" if italic else "")
        )
        tmp_path = f'{TMP_DIR}/{name_no_spaces.replace(FAMILY, "Tmp")}.ttf'

        # generation process
        print(f"\n[{name}]")
        if italic:
            # generate italic
            self.generate_italic(name, slim, weight, tmp_path)
        else:
            # generate upright
            self.generate_upright(name, slim, weight, tmp_path)

        if nerd:
            print("Applying nerd fonts patch...")
            cmd = [
                "fontforge",
                "-quiet",
                "-script",
                NERD_PATCHER,
                tmp_path,
                "--quiet",
                "--complete",
                "--careful",
                "-out",
                TMP_DIR,
            ]
            with ErrorSuppressor.suppress():
                with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
                    for line in proc.stdout:
                        print("  " + line.decode(), end="")
            if proc.returncode != 0:
                sys.exit(f'Error: patcher did not finish successfully for "{name}"')
            tmp_path = tmp_path.replace("-", "NerdFont-")

        print("Setting font parameters (1/2)...")
        with ErrorSuppressor.suppress():
            frpl = fontforge.open(tmp_path)
        frpl.familyname = family
        frpl.fontname = name_no_spaces
        frpl.fullname = name
        frpl.version = VERSION
        frpl.sfntRevision = float(VERSION)
        frpl.appendSFNTName("English (US)", "UniqueID", f"{VERSION};{name_no_spaces}")
        frpl.appendSFNTName("English (US)", "Version", f"Version {VERSION}")
        frpl.generate(tmp_path)
        frpl.close()

        print("Setting font parameters (2/2)...")
        frcd = TTFont(SRC_FILES[weight][0])
        frpl = TTFont(tmp_path)
        w = frcd["OS/2"].xAvgCharWidth
        frpl["OS/2"].xAvgCharWidth = int(w * SLIM_SCALE) if slim else w
        frpl["post"].isFixedPitch = 1  # for macOS
        if italic:
            frpl["OS/2"].fsSelection &= ~(1 << 6)  # clear REGULAR bit
            frpl["OS/2"].fsSelection |= 1 << 0  # set ITALIC bit
            frpl["head"].macStyle |= 1 << 1  # set Italic bit
        out_path = f"{OUT_DIR}/{name_no_spaces}.ttf"
        frpl.save(out_path)
        frcd.close()
        frpl.close()

        print(f"Generation complete! (=> {out_path})")

    def generate_upright(
        self,
        name: str,
        slim: bool,
        weight: str,
        out_path: str,
    ):
        frcd_path = SRC_FILES[weight][0]
        plex_path = SRC_FILES[weight][1]

        # check if src font files exist
        required(name, [frcd_path, plex_path])

        with ErrorSuppressor.suppress():
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
            is_plex_preferred = chr(i) in PLEX_PREFERRED_GLYPHS
            if is_plex_preferred or (i in plex and i not in frcd):
                plex.selection.select(("more",), i)
                frcd.selection.select(("more",), i)
            if is_plex_preferred:
                frcd[i].unlinkThisGlyph()
        plex.copy()
        frcd.paste()

        print("Transforming glyphs...")
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

    def generate_italic(
        self,
        name: str,
        slim: bool,
        weight: str,
        out_path: str,
    ):
        frcd_path = SRC_FILES[weight][0]
        plex_path = SRC_FILES[weight][1]
        glyph_paths = ITALIC_FILES[weight]

        # check if src font files exist
        required(name, [frcd_path, plex_path])
        required(name, list(glyph_paths.values()))

        with ErrorSuppressor.suppress():
            frcd = fontforge.open(frcd_path)

        # unlink all reference
        frcd.selection.all()
        frcd.unlinkReferences()

        print("Importing italic glyphs...")
        for g in ITALIC_GLYPHS:
            frcd[g].clear()
            frcd[g].importOutlines(glyph_paths[g])
            frcd[g].width = frcd["A"].width
            frcd.selection.select(("less",), g)

        print("Skewing glyphs (1/2)...")
        # all glyphs except italic glyphs
        frcd.transform(
            psMat.compose(
                psMat.translate(ITALIC_OFFSET * SLIM_SCALE, 0),
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
            sys.exit(f'Error: ttfautohint did not finish successfully for "{name}"')

        with ErrorSuppressor.suppress():
            frcd = fontforge.open(f"{out_path}.hinted")
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
            is_plex_preferred = chr(i) in PLEX_PREFERRED_GLYPHS
            if is_plex_preferred or (i in plex and i not in frcd):
                plex.selection.select(("more",), i)
                frcd.selection.select(("more",), i)
            if is_plex_preferred:
                frcd[i].unlinkThisGlyph()
        plex.copy()
        frcd.paste()

        print("Transforming glyphs...")
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

        print("Skewing glyphs (2/2)...")
        frcd.unlinkReferences()
        frcd.transform(
            psMat.compose(
                psMat.translate(ITALIC_OFFSET * SLIM_SCALE, 0),
                psMat.skew(math.radians(ITALIC_SKEW)),
            )
        )

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
        frcd.italicangle = -ITALIC_SKEW
        if not weight == "Regular":
            frcd.appendSFNTName("English (US)", "SubFamily", f"{weight} Italic")
        frcd.generate(out_path)
        frcd.close()
        plex.close()


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

    firple = Firple()

    if args.all or args.single is None:
        # generate all variants, weights and styles
        firple.generate(slim=False, bold=False, italic=False, nerd=args.nerd)  # Regular
        firple.generate(slim=False, bold=False, italic=True, nerd=args.nerd)  # Italic
        firple.generate(slim=False, bold=True, italic=False, nerd=args.nerd)  # Bold
        firple.generate(
            slim=False, bold=True, italic=True, nerd=args.nerd
        )  # Bold Italic
        firple.generate(
            slim=True, bold=False, italic=False, nerd=args.nerd
        )  # Slim Regular
        firple.generate(
            slim=True, bold=False, italic=True, nerd=args.nerd
        )  # Slim Italic
        firple.generate(slim=True, bold=True, italic=False, nerd=args.nerd)  # Slim Bold
        firple.generate(
            slim=True, bold=True, italic=True, nerd=args.nerd
        )  # Slim Bold Italic
    else:
        # generate a single font file with specified styles
        firple.generate(
            slim="slim" in args.single,
            bold="bold" in args.single,
            italic="italic" in args.single,
            nerd=args.nerd,
        )
