
.DEFAULT_GOAL := all

setup: scripts/downloader.py
	scripts/downloader.py --all

all: scripts/firple.py
	scripts/firple.py --all

clean:
	rm -rf __pycache__/ FontPatcher/ out/* tmp/ && find src/* | grep .ttf | xargs rm -rf