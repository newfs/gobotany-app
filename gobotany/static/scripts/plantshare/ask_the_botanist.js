/* Activate the Ask the Botanist section on either the PlantShare main
 * page or the Ask the Botanist page. */

define([
    'bridge/jquery',
    'plantshare/upload_modal',
    'util/shadowbox_init'
], function ($, upload_modal, Shadowbox) {

    var UPLOAD_SPINNER = '/static/images/icons/preloaders-dot-net-lg.gif';
    var DELETE_ICON = '/static/images/icons/close.png';

    $(document).ready(function () {

        function add_new_thumbnail(thumb_url, full_url, id) {
            var $lastImage = $('.thumb-gallery img.thumb').last();
            $lastImage.attr('src', thumb_url);
            $lastImage.wrap('<a href="' + full_url +
                '" class="preview"></a>');
            $lastImage.parent().after('<div class="delete-link"><a href="' +
                id + '"><img src="' + DELETE_ICON + '" /> Remove</a></div>');

            Shadowbox.setup('a.preview');
        }

        function remove_thumbnail(id, $frame) {
            console.log('Remove thumbnail ' + id);
            
            var rejectUrl = '/plantshare/api/image-reject/' + id;
            $.ajax(rejectUrl).done(function(data) {
                if(data.success) {
                    $('#sighting-photos').find('input[value=' + id +
                        ']').remove();
                    $frame.fadeOut(300, function() { $frame.remove(); });
                } else {
                    console.log('Error removing question image.');
                }
            });
        }

        function attach_question_image(new_image_id) {
            $('.template-image').clone().removeClass('template-image').attr({
                'name': 'question_images',
                'value': new_image_id
            }).appendTo('#question-images');
        }

        function start_upload() {
            $('.thumb-gallery').append(
                '<div class="thumb-frame"><img class="thumb" src="' + 
                UPLOAD_SPINNER + '"></div>');
        };

        function uploaded(info) {
            console.log('Successfully uploaded question image.');
            console.log('New image [id=' + info.id + ', thumb=' +
                        info.thumb + ', url=' + info.url + ']');
            add_new_thumbnail(info.thumb, info.url, info.id);
            attach_question_image(info.id);
        };

        function upload_error(error_info) {
            console.log('Error: ' + error_info);
        };

        $('.delete-link a').live('click', function() {
            $this = $(this);
            console.log('Remove image');
            $frame = $('.thumb-gallery .thumb-frame').has($this);
            remove_thumbnail($this.attr('href'), $frame);

            return false;
        });

        upload_modal.setup('.image-modal', '#upload-link', {
            onStartUpload: start_upload,
            onUploadComplete: uploaded,
            onError: upload_error,
        });

        $('#question').on('keypress keyup', function () {
            var box_is_empty = ($(this).val() === '');
            var $button = $('#ask-button');
            $button.toggleClass('disabled', box_is_empty);
            $button.prop('disabled', box_is_empty);
        });

    });

});
