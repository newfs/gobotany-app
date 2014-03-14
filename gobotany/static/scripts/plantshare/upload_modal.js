define([
    'bridge/jquery', 
    'bridge/jquery.form',
    'bridge/jpegmeta',
], function($, jqueryForm, JpegMeta) {

    var EMPTY_FILE_PATH = 'None Selected';
    var EMPTY_IMAGE_URL = '/static/images/icons/no-image.png';

    function get_gps(data, filename) {
        // If the file is a JPEG image, extract any GPS coordinates so
        // they can be sent to the server after resizing the image.
        // (Currently we only bother to check JPEG images for GPS data.)
        try {
            jpeg = new JpegMeta.JpegFile(data, filename);
        } catch (e) {
            // In the event of an error, such as a file not being a
            // JPEG, cancel looking for GPS coordinates.
            console.error('Unable to get GPS coordinates:', e);
            return;
        }

        if (jpeg.gps && jpeg.gps.longitude) {
            var latitude = jpeg.gps.latitude.value;
            var longitude = jpeg.gps.longitude.value;
            console.log('latitude:', latitude);
            console.log('longitude:', longitude);
            // Put the values into hidden form fields.
            $('#id_latitude').val(latitude);
            $('#id_longitude').val(longitude);
        }
    }

    function resize(image, $thumbnail_element) {
        var MAX_WIDTH = 1000;
        var MAX_HEIGHT = 1000;
        var width = image.width;
        var height = image.height;
        console.log('width:', width);
        console.log('height:', height);

        if (width > height) {
            if (width > MAX_WIDTH) {
                height = height * (MAX_WIDTH / width);
                width = MAX_WIDTH;
            }
        } else {
            if (height > MAX_HEIGHT) {
                width = width * (MAX_HEIGHT / height);
                height = MAX_HEIGHT;
            }
        }
        var canvas = document.getElementById('image_canvas');
        canvas.width = width;
        canvas.height = height;
        console.log('canvas:', canvas);
        var context = canvas.getContext('2d');
        console.log('image:', image);
        context.drawImage(image, 0, 0, width, height);
        console.log('image resized to ' + width + ' px wide and ' +
            height + ' px high');

        // Copy the resized image back to the thumbnail element for upload.
        $thumbnail_element.attr('src', canvas.toDataURL());
    }

    function setup(modalSelector, linkSelector, options) {
        var $modal = $(modalSelector);
        var $link = $(linkSelector);
        var $lastTrigger = null;
        var settings = $.extend({
            'onUploadComplete': function(imageInfo) {},
            'onError': function(errorInfo) {},
            'onStartUpload': function() {},
        }, options);

        // Set up overlay handling for any dynamic links
        // matching the selector
        $(document).on('click', linkSelector, function(e) {
            e.preventDefault();
            $lastTrigger = $(this);

            $lastTrigger.overlay({
                mask: {
                    color: 'black',
                    loadSpeed: 200,
                    opacity: 0.8
                },
                closeOnClick: false,
                load: true
            });
        });

        // Update filename box, image, and buttons when the selected file
        // changes.
        $modal.find('input[type="file"]').change(function() {
            var reader = new FileReader();
            var $thumbnail_image = $modal.find('img');
            var $hidden_image = $modal.find('#hidden_image');
            var files = this.files;

            reader.onloadend = function (e) {
                var image_result = e.target.result;
                $thumbnail_image.attr('src', image_result);
                $hidden_image.attr('src', image_result);
                
                // Try getting EXIF GPS data from the file.
                get_gps(atob(image_result.replace(/^.*?,/,'')), files[0]);

                // Resize the file so uploads will not take too long.
                resize($hidden_image[0], $thumbnail_image);
            }

            // Read the file that the user picked.
            reader.readAsDataURL(files[0]);

            // For security reasons, all browsers will report our file input box's file
            // path as C:\fakepath\<filename> so just strip off the fake path
            var path = $(this).val().replace(/C:\\fakepath\\/i, '');
            if(path) {
                $modal.find('.file-path').text(path);
                $modal.find('#upload-image-submit').removeClass('disabled');
            } else {
                $avatar_image.attr('src', EMPTY_IMAGE_URL);
                $modal.find('.file-path').text(EMPTY_FILE_PATH);
                $modal.find('#upload-image-submit').addClass('disabled');
            }
        });

        // Choose File button
        $modal.find('.file-select').click(function() {
            $modal.find('input[type="file"]').click();
        });

        // Close button
        $modal.find('.close').click(function() {
            $lastTrigger.overlay().close();
            return false;
        });

        // Submit button
        $modal.find('#upload-image-submit').click(function() {
            $modal.find('#upload-image-form').ajaxSubmit(function(response) {
                if(response.success) {
                    console.log('Upload complete');
                    var imageInfo = {
                        'id': response.id,
                        'thumb': response.thumb,
                        'url': response.url,
                        'latitude': response.latitude,
                        'longitude': response.longitude
                    };
                    settings.onUploadComplete.call(this, imageInfo, $lastTrigger); 
                } else {
                    console.log('Error during upload: ' + response.info);
                    settings.onError.call(this, response.info, $lastTrigger);
                }
            });
            $lastTrigger.overlay().close();
            settings.onStartUpload.call(this, $lastTrigger);
            return false;
        });
    }

    var obj = {
        setup: setup,
    };

    return obj;
});

