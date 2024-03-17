all: build-image download-source-font build-font

build-image:
	docker build -t font-builder:latest .

download-source-font:
	docker run --rm -v ${PWD}:/opt font-builder:latest /bin/bash -c "rm -rf ./src && ./download.py"

build-font:
	docker run --rm -v ${PWD}:/opt font-builder:latest /bin/bash -c "rm -rf ./out && ./build.py"

