#!/usr/bin/env python3

import argparse
import fontforge
import math
import os
import psMat
import shutil
import subprocess
import sys
from fontTools.ttLib import TTFont

from config import *



class ErrorSupressor:
    enable = True

    def __enter__(self):
        if ErrorSupressor.enable:
            fd_null = os.open('/dev/null', os.O_WRONLY)
            self.fd_stderr_copy = os.dup(2)
            os.dup2(fd_null, 2)
            os.close(fd_null)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if ErrorSupressor.enable:
            os.dup2(self.fd_stderr_copy, 2)
            os.close(self.fd_stderr_copy)


def main():
    print(FAMILY + ' Generator v' + VERSION)

    if not files_exist([NERD_PATCHER]):
        print(f'Error: missing required files for nerd fonts patching', file=sys.stderr)
        return

    # create directories
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    generate()

    # remove tmp directory
    shutil.rmtree(TMP_DIR)


def files_exist(paths: list) -> bool:
    exist = True
    for path in paths:
        if not os.path.exists(path):
            print(f'Error: file not found: "{path}"', file=sys.stderr)
            exist = False
    return exist


# def generate(slim: bool, bold: bool, italic: bool, nerd: bool) -> bool:
def generate() -> bool:
    family = FAMILY
    weight = 'SemiBold'
    name = family + ' ' + weight
    name_without_space = family.replace(' ', '')
    frcd_path = SRC_FILES[weight][0]
    plex_path = SRC_FILES[weight][1]
    out_path = f'{TMP_DIR}/{name_without_space.replace(FAMILY, "Tmp")}.ttf'

    # generation process
    print(f'\n[{name}]')

    # generate upright
    ok = generate_upright(name, weight, frcd_path, plex_path, out_path)
    if not ok:
        return False

    # Nerdfont
    print('Applying nerd fonts patch...')
    cmd = ['fontforge', '-quiet', '-script', NERD_PATCHER, out_path,
           '--quiet', '--complete', '--careful', '-out', TMP_DIR]
    with ErrorSupressor(), subprocess.Popen(cmd, stdout=subprocess.PIPE) as proc:
        for line in proc.stdout:
            print('  ' + line.decode(), end='')
    if not proc.returncode == 0:
        print(f'Error: patcher did not finish successfully for "{name}"',
              file=sys.stderr)
        return False

    print('Setting font parameters (1/2)...')
    with ErrorSupressor():
        frpl = fontforge.open(out_path)
    frpl.familyname = family
    frpl.fontname = name_without_space
    frpl.fullname = name
    frpl.version = VERSION
    frpl.sfntRevision = float(VERSION)
    frpl.appendSFNTName('English (US)', 'UniqueID',
                        f'{VERSION};{name_without_space}')
    frpl.appendSFNTName('English (US)', 'Version', f'Version {VERSION}')
    frpl.generate(out_path)
    frpl.close()

    print('Setting font parameters (2/2)...')
    frcd = TTFont(frcd_path)
    frpl = TTFont(out_path)
    frpl['post'].isFixedPitch = 1             # for macOS
    out_path = f'{OUT_DIR}/{name_without_space}.ttf'
    frpl.save(out_path)
    frcd.close()
    frpl.close()

    print(f'Generation complete! (=> {out_path})')

    return True


def generate_upright(name: str, weight: str, frcd_path: str, plex_path: str, out_path: str) -> bool:
    # check if src font files exist
    if not files_exist([frcd_path, plex_path]):
        print(f'Error: missing required files for "{name}"', file=sys.stderr)
        return False

    with ErrorSupressor():
        frcd = fontforge.open(frcd_path)
        plex = fontforge.open(plex_path)
    half_width = frcd['A'].width
    full_width = half_width * 2

    print('Copying glyphs...')
    plex.selection.none()
    frcd.selection.none()

    for i in range(sys.maxunicode + 1):
        if i in plex and not i in frcd or chr(i) in PLEX_PREFERRED_GLYPHS:
            plex.selection.select(('more', ), i)
            frcd.selection.select(('more', ), i)
        if chr(i) in PLEX_PREFERRED_GLYPHS:
            frcd[i].unlinkThisGlyph()
    
    plex.copy()
    frcd.paste()

    print('Transforming glyphs...')
    for glyph in frcd.selection.byGlyphs:
        scaled = glyph.width * PLEX_SCALE
        width = full_width if scaled > half_width else half_width
        offset = (width - scaled) / 2
        glyph.transform(psMat.compose(
            psMat.scale(PLEX_SCALE), psMat.translate(offset, 0)))
        glyph.width = width

    print('Generating temporary file...')
    frcd.fullname = name.replace(FAMILY, 'Tmp')
    frcd.weight = weight
    frcd.copyright = f'{COPYRIGHT}\n{frcd.copyright}\n{plex.copyright}'
    frcd.os2_unicoderanges = tuple(
        a | b for a, b in zip(frcd.os2_unicoderanges, plex.os2_unicoderanges))
    frcd.os2_codepages = tuple(
        a | b for a, b in zip(frcd.os2_codepages, plex.os2_codepages))
    frcd.generate(out_path)
    frcd.close()
    plex.close()

    return True

if __name__ == '__main__':
    main()
