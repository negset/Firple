import fontforge
import psMat
from fontTools.ttLib import TTFont
import argparse
import sys
from operator import or_

parser = argparse.ArgumentParser()
parser.add_argument('weight')
parser.add_argument('plex_path')
parser.add_argument('fira_path')
args = parser.parse_args(sys.argv[1:])

familyname = 'Firple'
weight = args.weight
version = '1.300'
copyright = 'Copyright 2021 negset'

plex_path = args.plex_path
fira_path = args.fira_path
firple_path = f'{familyname}-{weight}.ttf'

plex = fontforge.open(plex_path)
fira = fontforge.open(fira_path)

scale = 1.9
half_width = fira['A'].width
full_width = half_width * 2
overwrite_glyphs = ['「', '」']

print(f'### {familyname} {weight} ###')

print('# Copying glyphs...')
for i in range(0x10ffff + 1):
    if plex.__contains__(i) and not fira.__contains__(i):
        plex.selection.select(i)
        fira.selection.select(i)
        plex.copy()
        fira.paste()
for glyph in overwrite_glyphs:
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
fira.familyname = familyname
fira.fontname = f'{familyname}-{weight}'
fira.fullname = f'{familyname} {weight}'
fira.weight = weight
fira.version = version
fira.copyright = f'{copyright}\n{fira.copyright}\n{plex.copyright}'
fira.sfntRevision = None
fira.appendSFNTName('English (US)', 'UniqueID',
                    f'{version};{familyname}-{weight}')
fira.appendSFNTName('English (US)', 'Version', f'Version {version}')
fira.os2_unicoderanges = tuple(
    map(or_, plex.os2_unicoderanges, fira.os2_unicoderanges))
fira.os2_codepages = tuple(map(or_, plex.os2_codepages, fira.os2_codepages))

print('# Generating fonts...')
fira.generate(firple_path)

print('# Fixing char width...')
fira = TTFont(fira_path)
firple = TTFont(firple_path)
firple['OS/2'].xAvgCharWidth = fira['OS/2'].xAvgCharWidth
firple.save(firple_path)
