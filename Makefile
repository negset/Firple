
.DEFAULT_GOAL := all

setup: downloader.py
	./downloader.py --all

all: firple.py
	./firple.py --all

clean:
	rm -rf __pycache__/ FontPatcher/ out/* tmp/ && find src/* | grep .ttf | xargs rm -rf