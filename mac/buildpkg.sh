#!/bin/bash

cd ..
make DESTDIR=../mac/tmp/ install

/Developer/Applications/Utilities/PackageMaker.app/Contents/MacOS/PackageMaker -r mac/tmp/ -o mac/gutenbach.mpkg -i com.sipb -k -s mac/script -e mac/resources

