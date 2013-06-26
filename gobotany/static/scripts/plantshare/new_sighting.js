define([
    'bridge/jquery', 
    'bridge/jquery.form',
    'plantshare/upload_modal',
    'mapping/geocoder',
    'util/shadowbox_init'
], function ($, jqueryForm, upload_modal, Geocoder, Shadowbox) {

    var UPLOAD_SPINNER = '/static/images/icons/preloaders-dot-net-lg.gif';
    var DELETE_ICON = '/static/images/icons/close.png';

    $(document).ready(function () {

        function add_new_thumb(thumb_url, full_url, id) {
            // Set the last image's URL, which should be the spinner,
            // to the real image URL.
            var $last_image = $('.thumb-gallery img.thumb').last();
            $last_image.attr('src', thumb_url);
            $last_image.wrap('<a href="' + full_url +
                '" class="preview"></a>');
            $last_image.parent().after('<div class="delete-link"><a href="' +
                id + '"><img src="' + DELETE_ICON + '" /> Remove</a></div>');

            Shadowbox.setup('a.preview');
        }

        function remove_thumb(id, $frame) {
            console.log('Remove thumb ' + id);

            var reject_url = '/plantshare/api/image-reject/' + id;
            $.ajax(reject_url).done(function (data) {
                if(data.success) {
                    $('#sighting-photos').find('input[value=' + id +
                        ']').remove();
                    $frame.fadeOut(300, function () { $frame.remove(); });
                } else {
                    console.log('Error removing sighting photo.');
                }
            });
        }

        function attach_sighting_photo(new_photo_id) {
            $('.template-photo').clone().removeClass('template-photo').attr({
                    'name': 'sightings_photos',
                    'value': new_photo_id
                }).appendTo('#sighting-photos');
        }

        function start_upload() {
            // Add the spinner to the gallery
            $('.thumb-gallery').append(
                '<div class="thumb-frame"><img class="thumb" src="' + 
                UPLOAD_SPINNER + '"></div>');
        }

        function photo_uploaded(info) {
            console.log('Successfully uploaded sighting photo.');
            console.log('New Photo [id=' + info.id + ', thumb=' +
                        info.thumb + ', url=' + info.url + ']');
            add_new_thumb(info.thumb, info.url, info.id);
            attach_sighting_photo(info.id);
            if ((info.latitude !== null) && (info.longitude !== null)) {
                var $location = $('#id_location');
                $location.val(info.latitude + ', ' + info.longitude);
                $location.trigger('blur');   // trigger map update
            }
        }

        function upload_error(errorInfo) {
            console.log('Error: ' + errorInfo);
        }

        $('.delete-link a').live('click', function () {
            $this = $(this);
            console.log('Delete image');
            $frame = $('.thumb-gallery .thumb-frame').has($this);
            removeThumb($this.attr('href'), $frame);

            return false;
        });

        upload_modal.setup('.image-modal', '#upload-link', {
            onStartUpload: start_upload,
            onUploadComplete: photo_uploaded,
            onError: upload_error,
        });
    });

    function update_latitude_longitude(location, geocoder) {
        // Geocode the location unless it already looks like a pair of
        // coordinates.
        var lat_long_regex = new RegExp(
            '(^(-?(\\d{1,3}.?\\d{1,6}? ?[nNsS]?))([, ]+)' +
            '(-?(\\d{1,3}.?\\d{1,6}? ?[wWeE]?))$)');
        var latitude, longitude = '';
        if (lat_long_regex.test(location)) {
            // TODO: handle more advanced lat/long formats (this
            // currently only handles floats)
            var coordinates = location.replace(' ', '').split(',');
            latitude = coordinates[0];
            longitude = coordinates[1];
            $('#id_latitude').val(latitude);
            $('#id_longitude').val(longitude);
        }
        else {
            geocoder.geocode(location, function (results, status) {
                var lat_lng = geocoder.handle_response(results, status);
                latitude = lat_lng.lat();
                longitude = lat_lng.lng();
                $('#id_latitude').val(latitude);
                $('#id_longitude').val(longitude);
            });
        }
    }

    function set_visibility_restriction(is_restricted) {
        if (is_restricted) {
            // Show messages and restrict visibility options.
            $('.restricted').removeClass('hidden');
            $('#id_visibility').val('PRIVATE');
            $('#id_visibility option').each(function () {
                if ($(this).val() !== 'PRIVATE') {
                    $(this).attr('disabled', true);
                }
            });
        }
        else {
            // Hide messages and unrestrict visibility options.
            $('.restricted').addClass('hidden');
            $('#id_visibility option').each(function () {
                if ($(this).val() !== 'PRIVATE') {
                    $(this).attr('disabled', false);
                }
            });
        }
    }

    function check_restrictions(plant_name) {
        var is_restricted = false;
        var url = '/plantshare/api/restrictions/';
        url += '?plant=' + encodeURIComponent(plant_name);
        $.ajax({
            url: url
        }).done(function (json) {
            var is_restricted = false;
            // If any result says that sightings are restricted,
            // consider sightings restricted for this plant. (Multiple
            // results are for supporting common names, where the same
            // name can apply to more than one plant.)
            $.each(json, function (i, taxon) {
                if (taxon.sightings_restricted === true) {
                    is_restricted = true;
                    return false;   // to break out of the loop
                }
            });
            set_visibility_restriction(is_restricted);
        });
    }

    $(window).load(function () {   
        var geocoder = new Geocoder(); // geocoder must be created at onload
        var $identification_box = $('#id_identification');
        var $location_box = $('#id_location');
        
        // Check the conservation status for any initial identification
        // value.
        if ($identification_box.val() !== '') {
            check_restrictions($identification_box.val());
        }

        // Set the latitude and longitude for any initial location value.
        if ($location_box.val() !== '') {
            update_latitude_longitude($location_box.val(), geocoder);
        }

        // When the user enters a plant name in the identification
        // field, check the name to see if it is a plant with
        // conservation concerns. If so, the sighting will be hidden.
        $identification_box.on('blur', function () {
            check_restrictions($(this).val());
        });
        $identification_box.on('keyup', function (event) {
            if ($(this).val() === '') {
                // Empty box: clear any restriction message
                var is_restricted = false;
                set_visibility_restriction(is_restricted);
            }
            else if (event.which == 13) {   // Enter key
                check_restrictions($(this).val());
            }
        });

        // When the user enters a location, geocode it again if needed,
        // and let the map update.
        $location_box.blur(function () {
            update_latitude_longitude($(this).val(), geocoder);
        });
        $location_box.on('keypress keyup', function (event) {
            if (event.which === 13) {   // Enter key
                // If the location field is not empty, prevent the form
                // auto-submit so the user can see the map location update.
                // The location field, with its associated map, is similar to
                // textarea in the sense that Enter is used to accomplish
                // something within (or in this case, related to) it.
                var value = $(this).val();
                if (value !== '') {
                    event.preventDefault();
                    update_latitude_longitude(value, geocoder);
                    return false;
                }
            }
        });
    });

});
