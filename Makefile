
.DEFAULT_GOAL := all

setup: scripts/downloader.py
	scripts/downloader.py --all

all: scripts/firple.py
	scripts/firple.py --all

clean:
	rm -rf FontPatcher/ out/* scripts/__pycache__/ src/*.ttf tmp/
