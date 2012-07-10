#!/bin/bash

set -e

# usage: rebuild-thumbnails [limiting-pattern]
#
# For example, "rebuild-thumbnails '/[A-D]'" will rebuild the images for
# families starting with the letters A through D.

# Note that $base lacks its trailing slash so that we can add image
# dimensions to the directory name later!

source $(dirname "$0")/s3-init.sh
cd /tmp

pattern="${1:-.}"
base="s3://newfs/taxon-images"
base_length="${#base}"
alreadys="$(tempfile -p newfs)"

s3cmd ls "${base}/" | while read type family_url
do
    if [ "$type" != "DIR" ]; then continue; fi
    if ! echo "${family_url}" | grep -q "${pattern}"; then continue; fi

    # $family_url now looks like s3://newfs/taxon-images/Vitaceae/

    echo
    echo $family_url
    echo

    s3cmd ls "${family_url/taxon-images/taxon-images-239x239}" > "$alreadys"

    s3cmd ls "$family_url" | while read date time size url
    do
        # Like "/Acanthaceae/justicia-americana-fl-dhess.jpg":
        family_and_image="${url:$base_length+1}"

        if grep -q "$family_and_image"'$' "$alreadys"
        then
            echo "$family_and_image - already thumbnailed"
            continue
        fi

        echo $family_and_image - CREATING THUMBNAILS

        if [ "$date" == "DIR" ]; then continue; fi
        if [ "$url" != "${url%Thumbs.db}" ]; then
            s3cmd del "$url"
            continue
        fi
        s3cmd get --force "$url" image-$$.jpg

        convert image-$$.jpg \
            -thumbnail 160x149^ -gravity center -extent 160x149 -unsharp 0x.5 \
            -quality 90 image-$$b.jpg
        s3cmd put -P --add-header="Cache-Control: max-age=28800, public" \
            image-$$b.jpg "${base}-160x149/${family_and_image}"

        convert image-$$.jpg \
            -thumbnail 239x239^ -gravity center -extent 239x239 -unsharp 0x.5 \
            -quality 90 image-$$c.jpg
        s3cmd put -P --add-header="Cache-Control: max-age=28800, public" \
            image-$$c.jpg "${base}-239x239/${family_and_image}"

        # Note that the "s" in "1000s1000" means "scaled", because this
        # collection of images are not actually "1000x1000" pixels in
        # size; instead, only their longest dimension is 1000 pixels,
        # with the other dimension being chosen to keep the image's
        # relative dimensions and aspect ratio.

        convert image-$$.jpg \
            -resize 1000x1000 -unsharp 0x.5 \
            -quality 90 image-$$d.jpg
        s3cmd put -P --add-header="Cache-Control: max-age=28800, public" \
            image-$$d.jpg "${base}-1000s1000/${family_and_image}"

    done
done

rm -f "$alreadys"
