/* Checklist form utility functions */

define([
    'bridge/jquery',
], function ($) {

    function ChecklistForm() {
    };

    ChecklistForm.set_tab_order = function () {
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

    return ChecklistForm;
});
