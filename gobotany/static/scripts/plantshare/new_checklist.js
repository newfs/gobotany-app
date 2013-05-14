define([
    'bridge/jquery', 
    'util/shadowbox_init',
    'util/formset',
    'plantshare/upload_modal'
], function ($, Shadowbox, formset, upload_modal) {
    
    var UPLOAD_SPINNER = '/static/images/icons/preloaders-dot-net-lg.gif';

    var notes_modal = '' +
    '<div id="container" class="notes-modal">' +
		'<h1>Add Notes to Item</h1>' +
		'<section>' +
            '<textarea placeholder="Write your notes here"></textarea>' +
            '<div class="form-actions">' +
                '<a href="#" class="ps-button save">Save</a>' +
                '<a href="#" class="clear-btn">Clear</a>' +
            '</div><!-- /.form-actions -->' +
		'</section>' +
	'</div><!--!/#container -->';

    $(document).ready(function() {

        formset.init({
            'formSelector': '#formset tr',
            'formTemplateSelector': '#form-template tr',
            'addLinkSelector': '.add-new-row',
            'removeLinkSelector': '.close-btn.row-btn'
        });

        // Shadowbox setup for Notes modal popups
        $(document).on('click', 'a.note-link', function(e) {
            e.preventDefault();
            var $this = $(this);
            Shadowbox.open({
                content:  notes_modal,
                player: 'html',
                title: 'Checklist Notes',
                width: 550,
                height: 240,
                options: {
                    enableKeys: false,
                    onFinish: function(item) {
                        var $textarea = $('#container').find('textarea');
                        var $field = $this.parents('td.note').find('textarea');
                        $textarea.val($field.val());
                        $textarea.attr('rel', $field.attr('id'));
                    }
                }
            });
        });
        $(document).on('click', '.notes-modal a.save', function(e) {
            e.preventDefault();
            var $textarea = $(this).parents('section').find('textarea');
            var $field = $('#' + $textarea.attr('rel'));
            $field.val($textarea.val());
            Shadowbox.close();
        });
        $(document).on('click', '.notes-modal a.clear-btn', function(e) {
            e.preventDefault();
            $(this).parents('section').find('textarea').val('');
        });

        function startUpload(submitBtn, $trigger) {
            console.log('Beginning upload...');
            $trigger.html('<img src="' + UPLOAD_SPINNER + '" class="checklist-thumb" />');
        }

        function imageUploaded(imageInfo, $trigger) {
            console.log('Successfully uploaded checklist image');
            $trigger.html('<img src="' + imageInfo.thumb + '" class="checklist-thumb" />');
            $trigger.parent().find('input[type="hidden"]').val(imageInfo.id);
        }

        function uploadError(errorInfo, $trigger) {
            console.log('Checklist image upload error: ' + errorInfo);
        }

        upload_modal.setup('.image-modal', '.upload-image-thumb', {
            onUploadComplete: imageUploaded,
            onError: uploadError,
            onStartUpload: startUpload,
        });

    });
});
