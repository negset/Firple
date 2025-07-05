#!/usr/bin/env python3

import atexit
import itertools
import math
import os
import re
import shutil
import subprocess
import sys
from argparse import ArgumentParser, Namespace
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Iterable, Self

import fontforge
import psMat
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from settings import *

type FeatureData = tuple[str, tuple[tuple[str, tuple[str]]]]


@dataclass
class FontParams:
    slim: bool
    bold: bool
    italic: bool
    nerd: bool
    freeze_features: list[str]
    ext: str
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
        os.close(self.stderr_copy)

    @classmethod
    def suppress(cls) -> AbstractContextManager:
        return cls() if cls.enable else nullcontext()


def generate(params: FontParams) -> None:
    print(f"[{params.fullname}]")
    path = create_base_font(params)
    path = apply_auto_hinting(path, params)
    if params.nerd:
        path = apply_nerd_patch(path, params)
    path = set_font_params(path, params)
    print(f"Generation complete! => {path}\n")


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
                name: f"{SRC_DIR}/italic/{params.weight}/{name}.svg"
                for name in ITALIC_GLYPHS
            }
            # check if glyph files exist
            required(params.fullname, glyph_paths.values())

            print("Importing italic glyphs...")
            for name in ITALIC_GLYPHS:
                glyph = frcd[name]
                glyph.clear()
                glyph.importOutlines(glyph_paths[name], scale=False)
                glyph.width = frcd["A"].width

        if params.slim:
            print("Condensing glyphs...")
            frcd.selection.all()
            frcd.transform(psMat.scale(SLIM_SCALE, 1))

        print("Copying glyphs...")
        copied_slots = copy_glyphs(frcd, plex)

        print("Copying lookups...")
        copy_lookups(frcd, plex)

        print("Creating features...")
        for tag, names in FEATURE_GLYPHS.items():
            # check if glyph files exist
            glyph_paths = (
                f"{SRC_DIR}/{tag}/{params.weight}/{name}.{tag}.svg" for name in names
            )
            required(params.fullname, glyph_paths)
            f = freeze_feature if tag in params.freeze_features else create_feature
            copied_slots += f(tag, names, frcd, plex, params)

        print("Fixing scripts and languages of all features...")
        for lookup in frcd.gsub_lookups + frcd.gpos_lookups:
            _, _, old_feature_data_tuple = frcd.getLookupInfo(lookup)
            new_feature_data_tuple = tuple(
                feature_data_from_tag(tag) for tag, _ in old_feature_data_tuple
            )
            frcd.lookupSetFeatureList(lookup, new_feature_data_tuple)

        print("Transforming copied glyphs...")
        half_width = frcd["A"].width
        full_width = half_width * 2
        for slot in copied_slots:
            glyph = frcd[slot]
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
            offset = ITALIC_OFFSET * SLIM_SCALE if params.slim else ITALIC_OFFSET
            frcd.transform(
                psMat.compose(
                    psMat.translate(offset, 0),
                    psMat.skew(math.radians(ITALIC_SKEW)),
                )
            )

        print("Generating temporary file...")
        frcd.fullname = params.fullname.replace(FAMILY, "Tmp")
        # supress "Lookup subtable contains unused glyph..."
        with ErrorSuppressor.suppress():
            frcd.generate(out_path)

    return out_path


def copy_glyphs(
    frcd: fontforge.font,
    plex: fontforge.font,
) -> list[int]:
    # remove Plex prefered glyphs in advance
    for name in PLEX_PREFERRED_GLYPHS:
        frcd[name].unlinkThisGlyph()
        frcd.removeGlyph(name)
    # copy glyphs
    plex.selection.none()
    frcd.selection.none()
    for slot in range(len(plex)):  # pylint: disable=consider-using-enumerate
        print(f"\r| {int(round(100 * (slot + 1) / len(plex)))}%", end="")
        # within Unicode range
        if slot <= sys.maxunicode:
            if slot not in plex or slot in frcd:
                continue
            plex.selection.select(("encoding", "more"), slot)
            frcd.selection.select(("encoding", "more"), slot)
        # outside Unicode range
        else:
            if plex[slot].glyphname in frcd:
                # skip if name conflicts
                continue
            if any(s in plex[slot].glyphname for s in (".italic", ".prop")):
                # skip unneeded glyph
                continue
            if ".alt" in plex[slot].glyphname:
                if plex[slot].glyphname.split(".")[0] in frcd:
                    # skip if original of .alt is in FiraCode
                    continue
            plex.selection.select(("encoding", "more"), slot)
            glyph = frcd.createMappedChar(len(frcd))
            glyph.glyphname = plex[slot].glyphname
            frcd.selection.select(("encoding", "more"), glyph.encoding)
    print("\r| Done!")
    plex.copy()
    frcd.paste()
    return [slot for slot in frcd.selection]


def copy_lookups(
    frcd: fontforge.font,
    plex: fontforge.font,
) -> None:
    for slot in range(len(plex)):  # pylint: disable=consider-using-enumerate
        print(f"\r| {int(round(100 * (slot + 1) / len(plex)))}%", end="")
        if slot not in plex:
            continue
        for lookup in plex[slot].getPosSub("*"):
            subtable_name, lookup_type, *data = lookup
            if lookup_type in ["Position", "Pair"]:
                # skip gpos lookup
                continue
            lookup_name = plex.getLookupOfSubtable(subtable_name)
            lookup_info = plex.getLookupInfo(lookup_name)
            feature_tag = lookup_info[2][0][0] if lookup_info[2] else None
            if feature_tag and any(
                re.match(p, feature_tag) for p in (r"ss\d{2}", r"cv\d{2}")
            ):
                # skip stylistic sets and character variants
                continue
            # glyph is copied
            if slot in plex.selection:
                if feature_tag == "liga":
                    ligature_component_not_copied = False
                    # check if all ligature component is copied
                    for variant_name in data:
                        variant_glyph = plex[variant_name]
                        unicodes = [variant_glyph.unicode] + (
                            [u for u, _, _ in variant_glyph.altuni]
                            if variant_glyph.altuni
                            else []
                        )
                        if not (
                            variant_glyph.encoding in plex.selection
                            or all(unicode in plex.selection for unicode in unicodes)
                        ):
                            ligature_component_not_copied = True
                            break
                    # skip if ligature component is not copied
                    if ligature_component_not_copied:
                        continue
                try:
                    frcd.addLookup(lookup_name, *lookup_info, frcd.gsub_lookups[-1])
                    frcd.addLookupSubtable(lookup_name, subtable_name)
                except OSError:
                    pass  # already exists
                key = slot if slot <= sys.maxunicode else plex[slot].glyphname
                frcd[key].addPosSub(
                    subtable_name, data[0] if len(data) == 1 else tuple(data)
                )
            # glyph in not copied
            else:
                for variant_name in data:
                    variant_glyph = plex[variant_name]
                    unicodes = [variant_glyph.unicode] + (
                        [u for u, _, _ in variant_glyph.altuni]
                        if variant_glyph.altuni
                        else []
                    )
                    # variant glyph is copied
                    if variant_glyph.encoding in plex.selection or any(
                        unicode in plex.selection for unicode in unicodes
                    ):
                        # copy lookup if glyph exists in FiraCode
                        key = slot if slot <= sys.maxunicode else plex[slot].glyphname
                        if key in frcd:
                            try:
                                frcd.addLookup(
                                    lookup_name, *lookup_info, frcd.gsub_lookups[-1]
                                )
                                frcd.addLookupSubtable(lookup_name, subtable_name)
                            except OSError:
                                pass  # already exists
                            frcd[key].addPosSub(
                                subtable_name,
                                data[0] if len(data) == 1 else tuple(data),
                            )
    print("\r| Done!")


def create_feature(
    tag: str,
    glyph_names: list[str],
    frcd: fontforge.font,
    plex: fontforge.font,
    params: FontParams,
) -> list[int]:
    print(f"| Creating {tag} feature...")
    slots = []
    lookup_name = f"{tag} lookup"
    subtable_name = f"{tag} lookup subtable"
    frcd.addLookup(
        lookup_name,
        "gsub_single",
        None,
        (feature_data_from_tag(tag),),
        frcd.gsub_lookups[-1],
    )
    frcd.addLookupSubtable(lookup_name, subtable_name)

    for name in glyph_names:
        src_glyph = frcd[frcd.findEncodingSlot(name)]
        dst_name = f"{name}.{tag}"
        glyph = frcd.createChar(-1, dst_name)
        glyph.importOutlines(
            f"{SRC_DIR}/{tag}/{params.weight}/{dst_name}.svg",
            scale=False,
        )
        glyph.width = src_glyph.width
        glyph.transform(psMat.translate(0, plex.ascent - frcd.ascent))  # fix y gap
        src_glyph.addPosSub(subtable_name, dst_name)
        slots.append(glyph.encoding)
    return slots


def freeze_feature(
    tag: str,
    glyph_names: list[str],
    frcd: fontforge.font,
    plex: fontforge.font,
    params: FontParams,
) -> list[int]:
    print(f"| Freezing {tag} feature...")
    for name in glyph_names:
        glyph = frcd[frcd.findEncodingSlot(name)]
        original_width = glyph.width
        glyph.clear()
        glyph.importOutlines(
            f"{SRC_DIR}/{tag}/{params.weight}/{name}.{tag}.svg",
            scale=False,
        )
        glyph.width = original_width
        glyph.transform(psMat.translate(0, plex.ascent - frcd.ascent))  # fix y gap
    return []


def feature_data_from_tag(tag: str) -> FeatureData:
    # In FontForge, "dflt" refers to default LangSys table.
    return (tag, (("DFLT", ("dflt",)),))


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
        name_id_value_map = {
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
        for name_id, value in name_id_value_map.items():
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
        original_width = frcd["OS/2"].xAvgCharWidth
        frpl["OS/2"].xAvgCharWidth = (
            int(original_width * SLIM_SCALE) if params.slim else original_width
        )

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
            frac = Fraction(math.tan(math.radians(ITALIC_SKEW))).limit_denominator(1000)
            frpl["hhea"].caretSlopeRise = frac.denominator
            frpl["hhea"].caretSlopeRun = frac.numerator
            frpl["hhea"].caretOffset = ITALIC_OFFSET

        out_path = f"{OUT_DIR}/{params.psname}.{params.ext}"
        if params.ext in ["woff", "woff2"]:
            frpl.flavor = params.ext
        frpl.save(out_path)

    return out_path


def parse_arguments() -> Namespace:
    parser = ArgumentParser()
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
        choices=FEATURE_GLYPHS.keys(),
        default=[],
        nargs="*",
        help="freeze specified OpenType features",
    )
    parser.add_argument(
        "--ext",
        choices=["ttf", "otf", "woff", "woff2"],
        default="ttf",
        help="extension of the font to be output",
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


def required(obj: str, paths: Iterable[str]) -> None:
    missing = False
    for path in paths:
        if not os.path.exists(path):
            print(f'file not found: "{path}"', file=sys.stderr)
            missing = True
    if missing:
        sys.exit(f'Error: missing required files for "{obj}"')


def cleanup(keep_tmp_files: bool) -> None:
    # remove tmp directory
    if not keep_tmp_files and os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)


if __name__ == "__main__":
    print(f"{FAMILY} v{VERSION}\n")

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
        for slim, bold, italic in itertools.product([False, True], repeat=3):
            generate(
                FontParams(
                    slim=slim,
                    bold=bold,
                    italic=italic,
                    nerd=args.nerd,
                    freeze_features=args.freeze_features,
                    ext=args.ext,
                )
            )
    else:
        # generate a single font file as specified
        generate(
            FontParams(
                slim="slim" in args.single,
                bold="bold" in args.single,
                italic="italic" in args.single,
                nerd=args.nerd,
                freeze_features=args.freeze_features,
                ext=args.ext,
            )
        )
