
.DEFAULT_GOAL := all

setup: downloader.py
	./downloader.py --all

all: firple.py
	fontforge -quiet -script ./firple.py --all

clean:
	rm -rf __pycache__/ FontPatcher/ out/* tmp/ && find src/* | grep -v Firple | xargs rm -rf