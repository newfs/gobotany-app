define([
    'bridge/jquery', 
    'bridge/jquery.form',
], function($, jqueryForm) {

    var EMPTY_FILE_PATH = 'None Selected';
    var EMPTY_IMAGE_URL = '/static/images/icons/no-image.png';

    function setup(modalSelector, linkSelector, options) {
        var $modal = $(modalSelector);
        var $link = $(linkSelector);
        var settings = $.extend({
            'onUpload': function(imageInfo) {},
            'onError': function(errorInfo) {},
        }, options);

        var triggers = $link.overlay({
            mask: {
                color: 'black',
                loadSpeed: 200,
                opacity: 0.5
            },
            closeOnClick: false
        });

        // Update filename box, image, and buttons when the selected file
        // changes.
        $modal.find('input[type="file"]').change(function() {
            var reader = new FileReader();
            var $avatar_image = $modal.find('img');

            reader.onload = function(e) {
                $avatar_image.attr('src', e.target.result);
            }

            reader.readAsDataURL(this.files[0]);
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
            triggers.eq(0).overlay().close();
            return false;
        });

        // Submit button
        $modal.find('#upload-image-submit').click(function() {
            $modal.find('#upload-image-form').ajaxSubmit(function(response) {
                if(response.success) {
                    console.log('Upload complete');
                    var imageInfo = {
                        'id': response.id,
                        'thumb': response.thumb
                    };
                    settings.onUpload.call(this, imageInfo); 
                } else {
                    console.log('Error during upload: ' + response.info);
                    settings.onError.call(this, response.info);
                }
            });
            triggers.eq(0).overlay().close();
            return false;
        });
    }

    var obj = {
        setup: setup,
    };

    return obj;
});

