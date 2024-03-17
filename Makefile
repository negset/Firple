all: build-image build-font

build-image:
	docker build -t font-builder:latest .

build-font:
	docker run --rm -v ${PWD}:/opt font-builder:latest /bin/bash -c "rm -rf ./src ./out && ./downloader.py && ./firple.py"

