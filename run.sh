echo "**********************************************"
echo "* make Firple Regular / Italic               *"
echo "**********************************************"
fontforge -quiet -script make.py \
    'Regular' \
    'src/FiraCode-Regular.ttf' \
    'src/IBMPlexSansJP-Text.ttf' \
    'src/Firple-Italic.ttf'

echo "**********************************************"
echo "* make Firple Bold / Bold Italic             *"
echo "**********************************************"
fontforge -quiet -script make.py \
    'Bold' \
    'src/FiraCode-Bold.ttf' \
    'src/IBMPlexSansJP-Bold.ttf' \
    'src/Firple-BoldItalic.ttf'

echo "**********************************************"
echo "* make Firple Slim Regular / Italic          *"
echo "**********************************************"
fontforge -quiet -script make.py \
    --slim \
    'Regular' \
    'src/FiraCode-Regular.ttf' \
    'src/IBMPlexSansJP-Text.ttf' \
    'src/Firple-Italic.ttf'

echo "**********************************************"
echo "* make Firple Slim Bold / Bold Italic        *"
echo "**********************************************"
fontforge -quiet -script make.py \
    --slim \
    'Bold' \
    'src/FiraCode-Bold.ttf' \
    'src/IBMPlexSansJP-Bold.ttf' \
    'src/Firple-BoldItalic.ttf'