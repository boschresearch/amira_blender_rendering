
all: build install clean

build:
	# build package
	python setup.py build

install:
	# install package to current working environment
	python setup.py install

clean:
	# clean build and install artifacts
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist

