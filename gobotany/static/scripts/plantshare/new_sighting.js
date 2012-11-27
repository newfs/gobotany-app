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

        $('#upload-photo-submit').click(function() {
            $('#upload-photo-form').ajaxSubmit(function(json) {
                if(json.success) {
                    console.log('Successfully uploaded sighting photo.');
                } else {
                    console.log('Error: ' + json.info);
                }
            });
            $('.image-modal').hide();
            return false;
        });


    });


});

