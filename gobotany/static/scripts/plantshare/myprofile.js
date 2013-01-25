define([
    'bridge/jquery', 
    'bridge/jquery.form',
    'plantshare/upload_modal',
    'util/ajaxpartialform'
], function($, jqueryForm, upload_modal) {

    var UPLOAD_SPINNER = '/static/images/icons/preloaders-dot-net-lg.gif';

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

        function startUpload() {
            console.log('Beginning upload...');
            $('#avatar-image').attr('src', UPLOAD_SPINNER);
        }

        function avatarUploaded(imageInfo) {
            console.log('Successfully uploaded avatar');
            $('#avatar-image').attr('src', imageInfo.thumb);
        }

        function uploadError(errorInfo) {
            console.log('Avatar upload error: ' + errorInfo);
        }

        upload_modal.setup('.image-modal', '#upload-link', {
            onUploadComplete: avatarUploaded,
            onError: uploadError,
            onStartUpload: startUpload,
        });

    });

});
