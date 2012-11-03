#!/bin/bash

set -e

if [ -z "$1" ]
then
    echo usage: make-figures.sh path/to/book.pdf
    exit 2
fi

cd "$(dirname ${BASH_SOURCE[0]})"
cd ..
cd site
mkdir -p figures
cd figures
rm -f *.*
pdfimages "$1" image
for n in {1..944}
do
    image=image-$(printf '%03d' $[$n + 42])
    if [ -f "$image.pbm" ]
    then
        convert $image.pbm -negate -fill '#f0f0c0' -opaque white figure-$n.png
    else
        convert $image.ppm -fill '#f0f0c0' -opaque white figure-$n.png
    fi
done
