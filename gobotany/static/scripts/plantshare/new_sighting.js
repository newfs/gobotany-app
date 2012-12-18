define([
    'bridge/jquery', 
    'bridge/jquery.form',
    'mapping/geocoder',
], function ($, jqueryForm, Geocoder) {

    $(document).ready(function () {

        $('#upload-link').click(function () {
            imageModal = $('.image-modal');
            imageModal.show();
            return false;
        });

        $('.image-modal .close').click(function () {
            $('.image-modal').hide();
            return false;
        });

        function addNewThumb(url) {
            $('.thumb-gallery').prepend('<img class="thumb" src="' + url +
                                        '">');
        }

        function attachSightingPhoto(newPhotoId) {
            $('.template-photo').clone().removeClass('template-photo').attr({
                    'name': 'sightings_photos',
                    'value': newPhotoId
                }).appendTo('#sighting-photos');
        }

        $('#upload-photo-submit').click(function () {
            $('#upload-photo-form').ajaxSubmit(function (json) {
                if(json.success) {
                    console.log('Successfully uploaded sighting photo.');
                    console.log('New Photo [id=' + json.id + ', thumb=' +
                                json.thumb + ']');
                    addNewThumb(json.thumb);
                    attachSightingPhoto(json.id);
                } else {
                    console.log('Error: ' + json.info);
                }
            });
            $('.image-modal').hide();
            return false;
        });

    });


    $(window).load(function () {   // geocoder must be created at onload

        var geocoder = new Geocoder();
        
        // test
        geocoder.geocode('Framingham, MA', function (results, status) {
            var lat_lng = geocoder.handle_response(results, status);
            console.log('Framingham, MA lat_lng:', lat_lng);
        });
    });

});

