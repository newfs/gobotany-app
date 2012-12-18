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
        var lat_long_regex = new RegExp(
            '(^(-?(\\d{1,3}.?\\d{1,6}? ?[nNsS]?))([, ]+)' +
            '(-?(\\d{1,3}.?\\d{1,6}? ?[wWeE]?))$)');

        // When the user enters a location, geocode it unless it already
        // looks like a pair of coordinates.
        $('#id_location').blur(function () {
            var location = $(this).val();

            var lat_lng_string = '';
            if (lat_long_regex.test(location)) {
                $('#id_location_coordinates').val(location);
            }
            else {
                geocoder.geocode(location, function (results, status) {
                    var lat_lng = geocoder.handle_response(results, status);
                    lat_lng_string = lat_lng.toString().slice(1, -1);
                    if (lat_lng_string === 'NaN, NaN') {
                        lat_lng_string = '';
                    }
                    $('#id_location_coordinates').val(lat_lng_string);
                });
            }
        });

    });

});

