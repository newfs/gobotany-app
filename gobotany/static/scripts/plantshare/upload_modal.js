define([
    'bridge/jquery', 
    'bridge/jquery.form',
], function ($, jqueryForm) {

    var EMPTY_FILE_PATH = 'None Selected';
    var EMPTY_IMAGE_URL = '/static/images/icons/no-image.png';
    var LOADING_IMAGE_URL = '/static/images/icons/preloaders-dot-net-lg.gif';

    function resize(image, $thumbnail_element) {
        var MAX_WIDTH = 1000;
        var MAX_HEIGHT = 1000;
        var width = image.width;
        var height = image.height;
        console.log('width:', width);
        console.log('height:', height);

        if ((width > MAX_WIDTH) || (height > MAX_HEIGHT)) {
            console.log('image larger than site max: resize');
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

            // Copy the resized image back to the original element for upload.
            $thumbnail_element.attr('src', canvas.toDataURL());
        }
    }

    function reset_dialog_controls($modal) {
        // Clear any thumbnail and filename, and disable the Upload button.
        $modal.find('img').attr('src', EMPTY_IMAGE_URL);
        $modal.find('.file-select').removeClass('disabled');
        $modal.find('#upload-image-submit').addClass('disabled');
        $modal.find('.file-path').text(EMPTY_FILE_PATH);
    }

    function setup(modalSelector, linkSelector, options) {
        var $modal = $(modalSelector);
        var $link = $(linkSelector);
        var $lastTrigger = null;
        var settings = $.extend({
            'onUploadComplete': function (imageInfo) {},
            'onError': function (errorInfo) {},
            'onStartUpload': function () {},
        }, options);

        // Set up overlay handling for any dynamic links
        // matching the selector
        $(document).on('click', linkSelector, function (e) {
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

            // Upon activating the dialog, reset its controls.
            reset_dialog_controls($modal);
        });

        // Update filename box, image, and buttons when the selected file
        // changes.
        $modal.find('input[type="file"]').change(function () {

            var reader = new FileReader();
            var $thumbnail_image = $modal.find('img');
            var $hidden_image = $modal.find('#hidden_image');
            var files = this.files;

            reader.onloadstart = function () {
                // Temporarily change the thumbnail area to a spinner.
                // (Known issue: animation is often blocked during load.)
                $thumbnail_image.attr('src', LOADING_IMAGE_URL);

                // Make the Choose File button appear disabled.
                $modal.find('.file-select').addClass('disabled');
            }

            reader.onloadend = function (e) {
                var image_result = e.target.result;
                $hidden_image.attr('src', image_result);
                
                // Wait just a bit before resizing the image, to give the
                // image enough time to be put into the hidden image element.
                setTimeout(function () {
                    // Resize the file so uploads will not take too long.
                    resize($hidden_image[0], $thumbnail_image);

                    // Enable the Upload button.
                    $modal.find('#upload-image-submit').removeClass(
                        'disabled');
                }, 1000);
            }

            // Read the file that the user picked.
            reader.readAsDataURL(files[0]);

            // For security reasons, all browsers will report our file
            // input box's file path as C:\fakepath\<filename> so just
            // strip off the fake path.
            var path = $(this).val().replace(/C:\\fakepath\\/i, '');
            if (path) {
                $modal.find('.file-path').text(path);
            } else {
                reset_dialog_controls($modal);
            }
        });

        // Choose File button
        $modal.find('.file-select').click(function () {
            // Activate the actual file form element.
            $modal.find('input[type="file"]').click();
        });

        // Close button
        $modal.find('.close').click(function () {
            $lastTrigger.overlay().close();
            return false;
        });

        // Submit button
        $modal.find('#upload-image-submit').click(function () {
            $modal.find('#upload-image-form').ajaxSubmit(function (response) {
                if(response.success) {
                    console.log('Upload complete');
                    var imageInfo = {
                        'id': response.id,
                        'thumb': response.thumb,
                        'url': response.url,
                        'latitude': response.latitude,
                        'longitude': response.longitude
                    };
                    settings.onUploadComplete.call(this, imageInfo,
                        $lastTrigger); 
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
