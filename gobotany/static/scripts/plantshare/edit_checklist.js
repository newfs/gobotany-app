define([
    'bridge/jquery', 
    'bridge/jquery-ui', 
    'util/shadowbox_init',
    'util/formset',
    'util/suggester',
    'plantshare/upload_modal'
], function ($, jqueryUI, Shadowbox, formset, Suggester, upload_modal) {

    var notes_modal = '' +
    '<div id="container" class="notes-modal">' +
		'<h1>Add Notes to Item</h1>' +
		'<section>' +
            '<textarea placeholder="Write your notes here"></textarea>' +
            '<div class="form-actions">' +
                '<a href="#" class="ps-button save orange-button caps">Save</a>' +
                '<a href="#" class="clear-btn">Clear</a>' +
            '</div><!-- /.form-actions -->' +
		'</section>' +
	'</div><!--!/#container -->';

    var UPLOAD_SPINNER = '/static/images/icons/preloaders-dot-net-lg.gif';

    $(document).ready(function() {

        function set_tab_order() {
            // Set the tab order on all existing checklist entry fields.
            var num_fields = 6; // Number of fields per entry row
            var next_index = 3; // The two previous: checklist name, comments
            $('#checklist-fillout tbody tr').each(function () {
                var field_selectors = ['td.name input', 'td.image a',
                    'td.date-sighted input', 'td.location input',
                    'td.date-posted input', 'td.note a.note-link'];
                for (var i = 0; i < field_selectors.length; i += 1) {
                    var $element = $(this).find(field_selectors[i]);
                    $element.attr('tabindex', next_index);
                    next_index += 1;
                }
            });
        }

        formset.init({
            'formSelector': '#formset tr',
            'formTemplateSelector': '#form-template tr',
            'addLinkSelector': '.add-new-row',
            'removeLinkSelector': '.close-btn.row-btn',
            'canDelete': true,
            'onAfterAddForm': set_tab_order
        });

        $('body').on('focus', 'input.date-input', function() {
            $(this).datepicker({dateFormat: 'mm/dd/yy'});
        });

        $('body').on('focus', 'input.suggest', function() {
            var suggester = new Suggester(this);
            suggester.setup();
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

        function startUpload($trigger) {
            console.log('Beginning upload...');
            $trigger.html('<img src="' + UPLOAD_SPINNER + '" class="checklist-thumb">');
        }

        function imageUploaded(imageInfo, $trigger) {
            console.log('Successfully uploaded checklist image');
            $trigger.html('<img src="' + imageInfo.thumb + '" class="checklist-thumb">');
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

        // Set the tab order on the existing checklist entry rows.
        set_tab_order();
    });
});
