define([
    'bridge/jquery', 
    'bridge/jquery.form',
    'util/ajaxpartialform'
], function($, jqueryForm) {

    var EMPTY_FILE_PATH = 'None Selected';
    var EMPTY_IMAGE_URL = '/static/images/icons/no-image.png';

    function hideEditFields() {
        $('div.edit').hide();
        $('div.display').show();
    }

    $(document).ready(function() {
        $('.edit-link').click(function(eventObj) {
            // Hide any existing form inputs
            syncFields();
            hideEditFields();

            var link = eventObj.target;
            var display_field = $('div.display').has(link);
            var edit_field = display_field.siblings('div.edit');
            display_field.hide();
            edit_field.show();

            return false;
        });

        $('.field-reset').click(function() {
            hideEditFields();
            return false;
        });

        function syncFields() {
            $('div.edit').each(function() {
                var $edit = $(this);
                var $field = $edit.find('.ajax-field input,select,textarea').first();
                var newValue = 'N/A';
                if($field.prop('tagName') == 'SELECT') {
                    newValue = $field.find(':selected').text();
                } else {
                    newValue = $field.val();
                }

                var $display = $edit.siblings('div.display').children('p').first();
                $display.find('span').text(newValue);
            });
        }

        function fieldReset() {
            var $field = this.first();
            syncFields();
        }

        function formSave(jsonResponse) {
            if(jsonResponse.success) {
                syncFields();
                hideEditFields();
            }
        }

        $('.ajax-partial').ajaxpartialform({
            'onFieldReset': fieldReset,
            'onSave': formSave
        });

        syncFields();

        var triggers = $('#upload-link').overlay({
            mask: {
                color: 'black',
                loadSpeed: 200,
                opacity: 0.5
            },
            closeOnClick: false
        });

        $('#upload-image-form input[type="file"]').change(function() {
            var reader = new FileReader();
            var $avatar_image = $('.image-modal img');

            reader.onload = function(e) {
                $avatar_image.attr('src', e.target.result);
            }

            reader.readAsDataURL(this.files[0]);
            // For security reasons, all browsers will report our file input box's file
            // path as C:\fakepath\<filename> so just strip off the fake path
            var path = $(this).val().replace(/C:\\fakepath\\/i, '');
            if(path) {
                $('.image-modal .file-path').text(path);
                $('.image-modal #upload-image-submit').removeClass('disabled');
            } else {
                $avatar_image.attr('src', EMPTY_IMAGE_URL);
                $('.image-modal .file-path').text(EMPTY_FILE_PATH);
                $('.image-modal #upload-image-submit').addClass('disabled');
            }
        });

        $('.image-modal .file-select').click(function() {
            console.log('File select button');
            $('.image-modal input[type="file"]').click();
        });

        $('.image-modal .close').click(function() {
            triggers.eq(0).overlay().close();
            return false;
        });

        $('#upload-image-submit').click(function() {
            $('#upload-image-form').ajaxSubmit(function(json) {
                if(json.success) {
                    console.log('Successfully uploaded avatar');
                    $('#avatar-image').attr('src', json.thumb);
                } else {
                    console.log('Error: ' + json.info);
                }
            });
            triggers.eq(0).overlay().close();
            return false;
        });
    });

});
