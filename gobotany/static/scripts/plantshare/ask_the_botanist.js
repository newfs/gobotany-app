/* Activate the Ask the Botanist section on either the PlantShare main
 * page or the Ask the Botanist page. */

define([
    'bridge/jquery',
    'plantshare/upload_modal',
    'util/shadowbox_init'
], function ($, upload_modal, Shadowbox) {

    var UPLOAD_SPINNER = '/static/images/icons/preloaders-dot-net-lg.gif';
    var DELETE_ICON = '/static/images/icons/close.png';

    function add_new_thumbnail(thumb_url, full_url, id) {
        var $lastImage = $('.thumb-gallery img.thumb').last();
        $lastImage.attr('src', thumb_url);
        $lastImage.wrap('<a href="' + full_url +
            '" class="preview"></a>');
        $lastImage.parent().after('<div class="delete-link"><a href="' +
            id + '"><img src="' + DELETE_ICON + '" /> Remove</a></div>');

        Shadowbox.setup('a.preview');
    }

    function remove_thumb(id, $frame) {
        console.log('Remove thumb ' + id);
        
        // TODO: URL path
        var rejectUrl = '/ps/api/image-reject/' + id;
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
                'name': 'question_image',
                'value': new_image_id
            }).appendTo('#question-image');
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

    upload_modal.setup('.image-modal', '#upload-link', {
        onStartUpload: start_upload,
        onUploadComplete: uploaded,
        onError: upload_error,
    });

});
