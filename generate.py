import fontforge
import psMat
from fontTools.ttLib import TTFont
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('weight')
parser.add_argument('plex_path')
parser.add_argument('fira_path')
args = parser.parse_args(sys.argv[1:])

familyname = 'Firple'
weight = args.weight
version = '1.100'
copyright = 'Copyright 2021 negset'

plex_path = args.plex_path
fira_path = args.fira_path
firple_path = '{}-{}.ttf'.format(familyname, weight)

plex = fontforge.open(plex_path)
fira = fontforge.open(fira_path)

scale = 1.9
half_width = fira['A'].width
full_width = half_width * 2
overwrite_glyphs = ['「', '」']

print('### {} {} ###'.format(familyname, weight))

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
    w = full_width if glyph.width * scale > half_width else half_width
    x = (w - glyph.width * scale) / 2
    glyph.transform(psMat.scale(scale))
    glyph.transform(psMat.translate(x, 0))
    glyph.width = w

print('# Setting font parameters...')
fira.familyname = familyname
fira.fontname = '{}-{}'.format(familyname, weight)
fira.fullname = '{} {}'.format(familyname, weight)
fira.weight = weight
fira.version = version
fira.copyright = '{}\n{}\n{}'.format(copyright, fira.copyright, plex.copyright)
fira.sfntRevision = None
fira.appendSFNTName('English (US)', 'UniqueID', '{};{}-{}'.format(version, familyname, weight))
fira.appendSFNTName('English (US)', 'Version', 'Version {}'.format(version))
fira.os2_unicoderanges = (-1073741073, 1791491577, 33554450, 0)
fira.os2_codepages = (1610743967, 0)

print('# Generating fonts...')
fira.generate(firple_path)

print('# Fixing char width...')
fira = TTFont(fira_path)
firple = TTFont(firple_path)
firple['OS/2'].xAvgCharWidth = fira['OS/2'].xAvgCharWidth
firple.save(firple_path)