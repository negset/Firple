import argparse
import math
from operator import or_
import os
import sys
import fontforge
import psMat
from fontTools.ttLib import TTFont

parser = argparse.ArgumentParser()
parser.add_argument('--slim', action='store_true')
parser.add_argument('weight')
parser.add_argument('fira_path')
parser.add_argument('plex_path')
parser.add_argument('orig_path')
args = parser.parse_args()

family = 'Firple'
if args.slim:
    family += ' Slim'
family_without_space = family.replace(' ', '')
weight = args.weight
version = '3.000'
copyright = 'Copyright 2021 negset'
plex_scale = 1.9
plex_preferred_glyphs = ['「', '」']
italic_skew = 12
italic_offset = -100
slim_scale = 0.8 if args.slim else 1

fira_path = args.fira_path
plex_path = args.plex_path
orig_path = args.orig_path
out_dir = 'out'
firple_path = f'{out_dir}/{family_without_space}-{weight}.ttf'
italic_path = f'{out_dir}/{family_without_space}-{weight}Italic.ttf'
if weight == 'Regular':
    italic_path = italic_path.replace(weight, '')


def main():
    make_out_dir()

    print(f'### {family} {weight} ###')
    generate()

    print(f'### {family} {weight} Italic ###')
    italicize()


def make_out_dir():
    try:
        os.makedirs(out_dir)
    except FileExistsError:
        pass


def generate():
    fira = fontforge.open(fira_path)
    plex = fontforge.open(plex_path)
    half_width = int(fira['A'].width * slim_scale)
    full_width = half_width * 2

    if args.slim:
        print('# Condensing glyphs...')
        fira.selection.all()
        fira.transform(psMat.scale(slim_scale, 1))

    print('# Copying glyphs...')
    plex.selection.none()
    fira.selection.none()
    for i in range(sys.maxunicode + 1):
        if i in plex and not i in fira or chr(i) in plex_preferred_glyphs:
            plex.selection.select(('more', ), i)
            fira.selection.select(('more', ), i)
        if chr(i) in plex_preferred_glyphs:
            fira[i].unlinkThisGlyph()
    plex.copy()
    fira.paste()

    print('# Transforming glyphs...')
    for glyph in fira.selection.byGlyphs:
        scaled = glyph.width * plex_scale
        width = full_width if scaled > half_width else half_width
        offset = (width - scaled) / 2
        glyph.transform(psMat.compose(
            psMat.scale(plex_scale), psMat.translate(offset, 0)))
        glyph.width = width

    print('# Setting font parameters...')
    fira.familyname = family
    fira.fontname = f'{family_without_space}-{weight}'
    fira.fullname = f'{family} {weight}'
    fira.weight = weight
    fira.version = version
    fira.copyright = f'{copyright}\n{fira.copyright}\n{plex.copyright}'
    fira.sfntRevision = float(version)
    fira.appendSFNTName('English (US)', 'UniqueID',
                        f'{version};{family_without_space}-{weight}')
    fira.appendSFNTName('English (US)', 'Version', f'Version {version}')
    fira.os2_unicoderanges = tuple(
        map(or_, plex.os2_unicoderanges, fira.os2_unicoderanges))
    fira.os2_codepages = tuple(
        map(or_, plex.os2_codepages, fira.os2_codepages))

    print('# Generating font file...')
    fira.generate(firple_path)

    print('# Fixing font parameters...')
    fira = TTFont(fira_path)
    firple = TTFont(firple_path)
    firple['OS/2'].xAvgCharWidth = int(
        fira['OS/2'].xAvgCharWidth * slim_scale)
    firple['post'].isFixedPitch = 1                     # for macOS
    firple.save(firple_path)


def italicize():
    firple = fontforge.open(firple_path)
    orig = fontforge.open(orig_path)

    if args.slim:
        print('# Condensing glyphs...')
        orig.selection.all()
        orig.transform(psMat.compose(
            psMat.scale(slim_scale, 1),
            psMat.skew(math.radians(italic_skew) -
                       math.atan(math.tan(math.radians(italic_skew)) * slim_scale))))
        for glyph in orig.glyphs():
            glyph.width = int(glyph.width * slim_scale)

    print('# Transforming glyphs...')
    firple.selection.all()
    firple.unlinkReferences()
    firple.transform(psMat.compose(
        psMat.translate(italic_offset * slim_scale, 0),
        psMat.skew(math.radians(italic_skew))))

    print('# Copying glyphs...')
    orig.selection.none()
    firple.selection.none()
    for i in range(sys.maxunicode + 1):
        if i in orig and i in firple:
            orig.selection.select(('more', ), i)
            firple.selection.select(('more', ), i)
    orig.copy()
    firple.paste()

    print('# Setting font parameters...')
    firple.italicangle = -italic_skew
    if weight == 'Regular':
        firple.fontname = f'{family_without_space}-Italic'
        firple.fullname = f'{family} Italic'
        firple.appendSFNTName('English (US)', 'UniqueID',
                              f'{version};{family_without_space}-Italic')
    else:
        firple.fontname = f'{family_without_space}-{weight}Italic'
        firple.fullname = f'{family} {weight} Italic'
        firple.appendSFNTName('English (US)', 'UniqueID',
                              f'{version};{family_without_space}-{weight}Italic')
        firple.appendSFNTName('English (US)', 'SubFamily', f'{weight} Italic')

    print('# Generating font file...')
    firple.generate(italic_path)

    print('# Fixing font parameters...')
    firple = TTFont(firple_path)
    italic = TTFont(italic_path)
    italic['OS/2'].xAvgCharWidth = firple['OS/2'].xAvgCharWidth
    italic['post'].isFixedPitch = 1                     # for macOS
    italic['OS/2'].fsSelection &= 0b1111111110111111    # disable REGULAR flag
    italic['OS/2'].fsSelection |= 0b0000000000000001    # enable ITALIC flag
    italic['head'].macStyle |= 0b0000000000000010       # enable Italic flag
    italic.save(italic_path)


if __name__ == '__main__':
    main()
