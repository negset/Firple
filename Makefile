.DEFAULT_GOAL := all

setup: scripts/downloader.py
	python3 scripts/downloader.py --all

all: scripts/firple.py
	python3 scripts/firple.py --all

web: scripts/firple.py
	python3 scripts/firple.py --all --disable-nerd-fonts --ext woff2

clean:
	rm -rf out/ scripts/__pycache__/ tmp/
