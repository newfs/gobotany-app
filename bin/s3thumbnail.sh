#!/bin/bash

set -e

# usage: rebuild-thumbnails [limiting-pattern]
#
# For example, "rebuild-thumbnails '/[A-D]'" will rebuild the images for
# families starting with the letters A through D.  If no limiting
# pattern is specified then "." is used, which matches all files.

# Note that $base lacks its trailing slash so that we can add image
# dimensions to the directory name later!

pattern="${1:-.}"
base="s3://newfs/taxon-images"
base_length="${#base}"

num_left_alone=0
num_rebuilt=0
num_created=0

while read -r type family_url
do
    if [ "$type" != "DIR" ]
    then continue
    fi
    if ! echo "${family_url}" | grep -q "${pattern}"
    then continue
    fi

    # $family_url now looks like s3://newfs/taxon-images/Vitaceae/

    echo
    echo $family_url
    echo

    THUMBS="$(s3cmd ls ${family_url/taxon-images/taxon-images-239x239})"

    while read -r image_date image_time image_size image_url
    do
        if [ "$image_date" == "DIR" -o "${image_url: -1}" == "/" ]  # directory
        then continue
        fi

        if [ "${image_url}" != "${image_url%Thumbs.db}" ]  # Mac thumbnail db
        then
            s3cmd del "${image_url}"
            continue
        fi

        # Make a string like "/Acanthaceae/justicia-americana-fl-dhess.jpg":
        family_and_image="${image_url:$base_length+1}"

        read thumb_date thumb_time thumb_size thumb_url < <(
            echo "$THUMBS" | grep "$family_and_image"'$')

        if [ -z "$thumb_date" ]
        then
            echo "$family_and_image - never thumbnailed - CREATING"
            num_created=$(( $num_created + 1 ))
        elif
            [[ "$thumb_date" < "$image_date" ||
               "$thumb_date" = "$image_date" &&
               "$thumb_time" < "$image_time" ]]
        then
            echo "$family_and_image - stale thumbnail - REBUILDING"
            num_rebuilt=$(( $num_rebuilt + 1 ))
        else
            echo "$family_and_image - already thumbnailed"
            num_left_alone=$(( $num_left_alone + 1 ))
            continue
        fi

        s3cmd get --force "${image_url}" image-$$.jpg

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

    done < <(s3cmd ls "${family_url}")

done < <(s3cmd ls "${base}/")

echo "Thumbnailing done! $num_created created, $num_rebuilt rebuilt, and \
$num_left_alone simply left alone."
