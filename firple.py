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
                self.generate_upright(
                    name, slim, weight, frcd_path, plex_path, upright_tmp_path
                )
            # generate italic
            self.generate_italic(
                name, slim, weight, upright_tmp_path, ital_path, out_path
            )
        else:
            # generate upright
            self.generate_upright(name, slim, weight, frcd_path, plex_path, out_path)

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
            with ErrorSuppressor.suppress():
                with subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
                    for line in proc.stdout:
                        print("  " + line.decode(), end="")
            if proc.returncode != 0:
                sys.exit(f'Error: patcher did not finish successfully for "{name}"')
            out_path = out_path.replace("-", "NerdFont-")

        print("Setting font parameters (1/2)...")
        with ErrorSuppressor.suppress():
            frpl = fontforge.open(out_path)
        frpl.familyname = family
        frpl.fontname = name_without_space
        frpl.fullname = name
        frpl.version = VERSION
        frpl.sfntRevision = float(VERSION)
        frpl.appendSFNTName(
            "English (US)", "UniqueID", f"{VERSION};{name_without_space}"
        )
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

    def generate_upright(
        self,
        name: str,
        slim: bool,
        weight: str,
        frcd_path: str,
        plex_path: str,
        out_path: str,
    ):
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

    def generate_italic(
        self,
        name: str,
        slim: bool,
        weight: str,
        frpl_path: str,
        ital_path: str,
        out_path: str,
    ):
        # check if src font files exist
        required(name, [frpl_path, ital_path])

        with ErrorSuppressor.suppress():
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
