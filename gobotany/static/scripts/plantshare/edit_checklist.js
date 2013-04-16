define([
    'bridge/jquery', 
    'util/shadowbox_init',
    'util/formset'
], function ($, Shadowbox, formset) {

    $(document).ready(function() {

        formset.init({
            'formSelector': '#formset tr',
            'formTemplateSelector': '#form-template tr',
            'addLinkSelector': '.add-new-row',
            'removeLinkSelector': '.close-btn.row-btn',
            'canDelete': true
        });

    });
});
