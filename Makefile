.DEFAULT_GOAL := all

setup: scripts/downloader.py
	./scripts/downloader.py --all

all: scripts/firple.py
	./scripts/firple.py --all

web: scripts/firple.py
	./scripts/firple.py --all --disable-nerd-fonts --ext woff2

clean:
	rm -rf FontPatcher/ out/* scripts/__pycache__/ src/*.ttf tmp/
