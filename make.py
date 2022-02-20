import argparse
import math
from operator import or_
import sys
import fontforge
import psMat
from fontTools.ttLib import TTFont

parser = argparse.ArgumentParser()
parser.add_argument('weight')
parser.add_argument('fira_path')
parser.add_argument('plex_path')
parser.add_argument('orig_path')
args = parser.parse_args()

family = 'Firple'
weight = args.weight
version = 2.100
copyright = 'Copyright 2021 negset'

fira_path = args.fira_path
plex_path = args.plex_path
orig_path = args.orig_path
firple_path = f'{family}-{weight}.ttf'
italic_path = f'{family}-Italic.ttf' if weight == 'Regular' else f'{family}-{weight}Italic.ttf'


def generate():
    plex = fontforge.open(plex_path)
    fira = fontforge.open(fira_path)
    scale = 1.9
    half_width = fira['A'].width
    full_width = half_width * 2
    overwrite_glyphs = ['「', '」']

    print(f'\n##### {family} {weight} #####')

    print('# Copying glyphs...')
    for i in range(sys.maxunicode + 1):
        if i in plex and not i in fira:
            plex.selection.select(i)
            fira.selection.select(i)
            plex.copy()
            fira.paste()
    for glyph in overwrite_glyphs:
        fira[ord(glyph)].unlinkThisGlyph()
        plex.selection.select(ord(glyph))
        fira.selection.select(ord(glyph))
        plex.copy()
        fira.paste()

    print('# Transforming glyphs...')
    fira.selection.changed()
    for glyph in fira.selection.byGlyphs:
        scaled = glyph.width * scale
        width = full_width if scaled > half_width else half_width
        trans = (width - scaled) / 2
        glyph.transform(psMat.compose(
            psMat.scale(scale), psMat.translate(trans, 0)))
        glyph.width = width

    print('# Setting font parameters...')
    fira.familyname = family
    fira.fontname = f'{family}-{weight}'
    fira.fullname = f'{family} {weight}'
    fira.weight = weight
    fira.version = str(version)
    fira.copyright = f'{copyright}\n{fira.copyright}\n{plex.copyright}'
    fira.sfntRevision = version
    fira.appendSFNTName('English (US)', 'UniqueID',
                        f'{version};{family}-{weight}')
    fira.appendSFNTName('English (US)', 'Version', f'Version {version}')
    fira.os2_unicoderanges = tuple(
        map(or_, plex.os2_unicoderanges, fira.os2_unicoderanges))
    fira.os2_codepages = tuple(
        map(or_, plex.os2_codepages, fira.os2_codepages))

    print('# Generating fonts...')
    fira.generate(firple_path)

    print('# Fixing font parameters...')
    fira = TTFont(fira_path)
    firple = TTFont(firple_path)
    firple['OS/2'].xAvgCharWidth = fira['OS/2'].xAvgCharWidth
    firple['post'].isFixedPitch = 1     # for macOS
    firple.save(firple_path)


def generate_italic():
    firple = fontforge.open(firple_path)
    orig = fontforge.open(orig_path)
    trans = -100
    skew = 12

    if weight == 'Regular':
        print(f'\n##### {family} Italic #####')
    else:
        print(f'\n##### {family} {weight} Italic #####')

    print('# Transforming glyphs...')
    mat = psMat.compose(psMat.translate(trans, 0),
                        psMat.skew(math.radians(skew)))
    firple.selection.all()
    firple.unlinkReferences()
    firple.transform(mat)

    print('# Copying glyphs...')
    for i in range(sys.maxunicode + 1):
        if i in orig and i in firple:
            orig.selection.select(i)
            firple.selection.select(i)
            orig.copy()
            firple.paste()

    print('# Setting font parameters...')
    firple.italicangle = -skew
    if weight == 'Regular':
        firple.fontname = f'{family}-Italic'
        firple.fullname = f'{family} Italic'
        firple.appendSFNTName('English (US)', 'UniqueID',
                              f'{version};{family}-Italic')
    else:
        firple.fontname = f'{family}-{weight}Italic'
        firple.fullname = f'{family} {weight} Italic'
        firple.appendSFNTName('English (US)', 'UniqueID',
                              f'{version};{family}-{weight}Italic')
        firple.appendSFNTName('English (US)', 'SubFamily', f'{weight} Italic')

    print('# Generating fonts...')
    firple.generate(italic_path)

    print('# Fixing font parameters...')
    firple = TTFont(firple_path)
    italic = TTFont(italic_path)
    italic['OS/2'].xAvgCharWidth = firple['OS/2'].xAvgCharWidth
    italic['post'].isFixedPitch = 1     # for macOS
    italic['OS/2'].fsSelection &= 0b1111111110111111    # disable REGULAR flag
    italic['OS/2'].fsSelection |= 0b0000000000000001    # enable ITALIC flag
    italic['head'].macStyle |= 0b0000000000000010       # enable Italic flag
    italic.save(italic_path)


generate()
generate_italic()
