#!/usr/bin/env python3

import atexit
import math
import os
import shutil
import subprocess
import sys
from argparse import ArgumentParser, Namespace
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field
from typing import Self

import fontforge
import psMat
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from settings import *


@dataclass
class FontParams:
    slim: bool
    bold: bool
    italic: bool
    nerd: bool
    freeze_features: list[str]
    family: str = field(init=False)
    weight: str = field(init=False)
    subfamily: str = field(init=False)
    fullname: str = field(init=False)
    psname: str = field(init=False)

    def __post_init__(self):
        self.family = f"{FAMILY} Slim" if self.slim else FAMILY
        self.weight = "Bold" if self.bold else "Regular"
        if self.italic:
            if self.weight == "Regular":
                self.subfamily = "Italic"
            else:
                self.subfamily = f"{self.weight} Italic"
        else:
            self.subfamily = self.weight
        self.fullname = f"{self.family} {self.subfamily}"
        self.psname = f"{self.family}-{self.subfamily}".replace(" ", "")


class FontForgeFont:
    def __init__(self, path) -> None:
        with ErrorSuppressor.suppress():
            self.font = fontforge.open(path)

    def __enter__(self) -> fontforge.font:
        return self.font

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.font.close()


class ErrorSuppressor:
    enable = False

    def __init__(self) -> None:
        # copy stderr
        self.stderr_copy = os.dup(2)

    def __enter__(self) -> Self:
        # replace stderr with null device
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
        os.close(devnull)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        # restore stderr
        os.dup2(self.stderr_copy, 2)

    @classmethod
    def suppress(cls) -> AbstractContextManager:
        return cls() if cls.enable else nullcontext()


def generate(params: FontParams) -> None:
    print(f"\n[{params.fullname}]")
    path = create_base_font(params)
    path = apply_auto_hinting(path, params)
    if params.nerd:
        path = apply_nerd_patch(path, params)
    path = set_font_params(path, params)
    print(f"Generation complete! (=> {path})")


def create_base_font(params: FontParams) -> str:
    frcd_path = SRC_FILES[params.weight][0]
    plex_path = SRC_FILES[params.weight][1]
    out_path = f'{TMP_DIR}/{params.psname.replace(FAMILY, "Tmp")}.ttf'

    # check if src font files exist
    required(params.fullname, [frcd_path, plex_path])

    with (
        FontForgeFont(frcd_path) as frcd,
        FontForgeFont(plex_path) as plex,
    ):
        if params.italic:
            glyph_paths = {
                c: f"{SRC_DIR}/italic/{params.weight}/{c}.svg" for c in ITALIC_CHARS
            }
            # check if glyph files exist
            required(params.fullname, list(glyph_paths.values()))

            print("Importing italic glyphs...")
            for c in ITALIC_CHARS:
                frcd[c].clear()
                frcd[c].importOutlines(glyph_paths[c])
                frcd[c].width = frcd["A"].width

        if params.slim:
            print("Condensing glyphs...")
            frcd.selection.all()
            frcd.transform(psMat.scale(SLIM_SCALE, 1))

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

        for tag, chars in FEATURE_CHARS.items():
            f = freeze_feature if tag in params.freeze_features else create_feature
            f(tag, chars, frcd, plex, params)

        print("Transforming copied glyphs...")
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

        if params.italic:
            print("Skewing glyphs...")
            frcd.selection.all()
            frcd.unlinkReferences()
            frcd.transform(
                psMat.compose(
                    psMat.translate(ITALIC_OFFSET * SLIM_SCALE, 0),
                    psMat.skew(math.radians(ITALIC_SKEW)),
                )
            )

        print("Generating temporary file...")
        frcd.fullname = params.fullname.replace(FAMILY, "Tmp")
        frcd.generate(out_path)

    return out_path


def create_feature(
    tag: str,
    chars: list[str],
    frcd: fontforge.font,
    plex: fontforge.font,
    params: FontParams,
) -> None:
    print(f"Creating {tag} feature...")
    glyph_paths = {c: f"{SRC_DIR}/{tag}/{params.weight}/{c}.{tag}.svg" for c in chars}
    # check if glyph files exist
    required(params.fullname, list(glyph_paths.values()))

    lookup_name = f"{tag} lookup"
    subtable_name = f"{tag} lookup subtable"
    feature_script_lang_tuple = (
        # In FontForge, "dflt" refers to default LangSys table.
        # "zinh" (inherited) and "zyyy" (undetermined) should not be used as script tags,
        # but FiraCode uses them, and some features will not work in some apps without them.
        (
            tag,  # feature_tag
            (
                ("DFLT", ("dflt",)),  # (script_tag, (language_system_tag, ...))
                ("latn", ("dflt",)),
                ("zinh", ("dflt",)),
                ("zyyy", ("dflt",)),
            ),
        ),
    )
    frcd.addLookup(
        lookup_name,
        "gsub_single",
        None,
        feature_script_lang_tuple,
        frcd.gsub_lookups[-1],
    )
    frcd.addLookupSubtable(lookup_name, subtable_name)

    for c in chars:
        g = frcd.createChar(-1, f"{c}.{tag}")
        g.importOutlines(
            f"{SRC_DIR}/{tag}/{params.weight}/{c}.{tag}.svg",
            scale=False,
        )
        g.width = frcd[c].width
        g.transform(psMat.translate(0, plex.ascent - frcd.ascent))  # fix y gap
        frcd.selection.select(("more",), g)
        frcd[c].addPosSub(subtable_name, f"{c}.{tag}")


def freeze_feature(
    tag: str,
    chars: list[str],
    frcd: fontforge.font,
    plex: fontforge.font,
    params: FontParams,
) -> None:
    print(f"Freezing {tag} feature...")
    glyph_paths = {c: f"{SRC_DIR}/{tag}/{params.weight}/{c}.{tag}.svg" for c in chars}
    # check if glyph files exist
    required(params.fullname, list(glyph_paths.values()))

    for c in chars:
        w = frcd[c].width
        frcd[c].clear()
        frcd[c].importOutlines(
            f"{SRC_DIR}/{tag}/{params.weight}/{c}.{tag}.svg",
            scale=False,
        )
        frcd[c].transform(psMat.translate(0, plex.ascent - frcd.ascent))  # fix y gap
        frcd[c].width = w


def apply_auto_hinting(path: str, params: FontParams) -> str:
    print("Hinting glyphs...")
    out_path = path.replace(".ttf", ".hinted.ttf")
    cmd = [
        "ttfautohint",
        "--no-info",
        "--ignore-restrictions",
        "--default-script=latn",
        "--fallback-script=none",
        "--fallback-scaling",
        path,
        out_path,
    ]
    cp = subprocess.run(cmd, check=False)
    if cp.returncode != 0:
        sys.exit(
            f'Error: ttfautohint did not finish successfully for "{params.fullname}"'
        )
    return out_path


def apply_nerd_patch(path: str, params: FontParams) -> str:
    # check if nerd fonts patcher exists
    required("nerd fonts patching", [NERD_PATCHER])

    print("Applying nerd fonts patch...")
    cmd = [
        "fontforge",
        "-quiet",
        "-script",
        NERD_PATCHER,
        path,
        "--complete",
        "--careful",
        "-out",
        TMP_DIR,
    ]
    last_line = None
    with (
        ErrorSuppressor.suppress(),
        subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, bufsize=1) as proc,
    ):
        assert proc.stdout is not None
        for line in proc.stdout:
            columns = shutil.get_terminal_size().columns
            text = f'\r| {line.rstrip("\n")}'.ljust(columns)[:columns]
            sys.stdout.write(text)
            sys.stdout.flush()
            last_line = line
        proc.wait()
        if proc.returncode != 0:
            sys.exit(
                f'Error: patcher did not finish successfully for "{params.fullname}"'
            )
        print()
    # last_line should be "    \===> 'out_path'"
    assert last_line is not None
    out_path = last_line.split("'")[1]
    return out_path


def set_font_params(path: str, params: FontParams) -> str:
    print("Setting font parameters...")
    with (
        TTFont(SRC_FILES[params.weight][0]) as frcd,
        TTFont(SRC_FILES[params.weight][1]) as plex,
        TTFont(path) as frpl,
    ):
        # name table
        frpl["name"].names = []  # clear
        name_id_to_value = {
            0: "; ".join(
                [
                    COPYRIGHT,
                    frcd["name"].names[0].toUnicode(),
                    plex["name"].names[0].toUnicode(),
                ]
            ),
            1: params.family,
            2: params.subfamily,
            3: f"{VERSION};{params.psname}",
            4: params.fullname,
            5: f"Version {VERSION}",
            6: params.psname,
        }
        for name_id, value in name_id_to_value.items():
            m_record = NameRecord()
            m_record.nameID = name_id
            m_record.platformID = 1  # Macintosh
            m_record.platEncID = 0  # Roman
            m_record.langID = 0  # English
            m_record.string = value.encode(m_record.getEncoding())
            frpl["name"].names.append(m_record)
            w_record = NameRecord()
            w_record.nameID = name_id
            w_record.platformID = 3  # Windows
            w_record.platEncID = 1  # Unicode BMP
            w_record.langID = 0x409  # en-US
            w_record.string = value.encode(w_record.getEncoding())
            frpl["name"].names.append(w_record)

        # meta table
        meta_table = newTable("meta")
        meta_table.data = {
            "dlng": "Hani, Hira, Hrkt, Jpan, Kana",  # ISO 15924
            "slng": "Hani, Hira, Hrkt, Jpan, Kana, Latn",  # ISO 15924
        }
        frpl["meta"] = meta_table

        # OS/2 ranges
        ranges = [
            "ulUnicodeRange1",
            "ulUnicodeRange2",
            "ulUnicodeRange3",
            "ulUnicodeRange4",
            "ulCodePageRange1",
            "ulCodePageRange2",
        ]
        for r in ranges:
            setattr(
                frpl["OS/2"], r, getattr(frcd["OS/2"], r) | getattr(plex["OS/2"], r)
            )

        # fix xAvgCharWidth changed by FontForge
        w = frcd["OS/2"].xAvgCharWidth
        frpl["OS/2"].xAvgCharWidth = int(w * SLIM_SCALE) if params.slim else w

        # others
        frpl["OS/2"].panose.bFamilyType = 2  # Latin Text and Display
        frpl["OS/2"].panose.bProportion = 9  # Monospaced
        frpl["post"].isFixedPitch = 1
        frpl["head"].fontRevision = float(VERSION)
        if params.italic:
            frpl["OS/2"].fsSelection &= ~(1 << 6)  # clear REGULAR bit
            frpl["OS/2"].fsSelection |= 1 << 0  # set ITALIC bit
            frpl["post"].italicAngle = -ITALIC_SKEW
            frpl["head"].macStyle |= 1 << 1  # set Italic bit

        out_path = f"{OUT_DIR}/{params.psname}.ttf"
        frpl.save(out_path)
    return out_path


def parse_arguments() -> Namespace:
    parser = ArgumentParser(description=f"{FAMILY} Generator v{VERSION}")
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="generate all families, weights, styles (default)",
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
        default=[],
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
        help="show FontForge error messages",
    )
    return parser.parse_args()


def required(obj: str, paths: list[str]) -> None:
    ok = True
    for path in paths:
        if not os.path.exists(path):
            print(f'file not found: "{path}"', file=sys.stderr)
            ok = False
    if not ok:
        sys.exit(f'Error: missing required files for "{obj}"')


def cleanup(keep_tmp_files: bool) -> None:
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
        # generate all families, weights, styles
        # Regular
        generate(FontParams(False, False, False, args.nerd, args.freeze_features))
        # Italic
        generate(FontParams(False, False, True, args.nerd, args.freeze_features))
        # Bold
        generate(FontParams(False, True, False, args.nerd, args.freeze_features))
        # Bold Italic
        generate(FontParams(False, True, True, args.nerd, args.freeze_features))
        # Slim Regular
        generate(FontParams(True, False, False, args.nerd, args.freeze_features))
        # Slim Italic
        generate(FontParams(True, False, True, args.nerd, args.freeze_features))
        # Slim Bold
        generate(FontParams(True, True, False, args.nerd, args.freeze_features))
        # Slim Bold Italic
        generate(FontParams(True, True, True, args.nerd, args.freeze_features))
    else:
        # generate a single font file as specified
        generate(
            FontParams(
                "slim" in args.single,
                "bold" in args.single,
                "italic" in args.single,
                args.nerd,
                args.freeze_features,
            )
        )
