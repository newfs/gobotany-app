define([
    'bridge/jquery', 
    'bridge/jquery.form',
], function($, jqueryForm) {

    $(document).ready(function() {

        $('#upload-link').click(function() {
            imageModal = $('.image-modal');
            imageModal.show();
            return false;
        });

        $('.image-modal .close').click(function() {
            $('.image-modal').hide();
            return false;
        });

        function addNewThumb(id, url) {
            $('.thumb-gallery').prepend('<img class="thumb" src="' + url + '" />');
        }

        $('#upload-photo-submit').click(function() {
            $('#upload-photo-form').ajaxSubmit(function(json) {
                if(json.success) {
                    console.log('Successfully uploaded sighting photo.');
                    console.log('New Photo [id=' + json.id + ', thumb=' + json.thumb + ']');
                    addNewThumb(json.id, json.thumb);
                } else {
                    console.log('Error: ' + json.info);
                }
            });
            $('.image-modal').hide();
            return false;
        });


    });


});

