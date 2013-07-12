define([
    'bridge/jquery',
], function ($) {

    var CHECKBOXES_SELECTOR = '#main input[type="checkbox"]';

    $(document).ready(function () {
    
        var num_checkboxes = $(CHECKBOXES_SELECTOR).length;

        function enable_disable_agree_button() {
            var num_checked = $(CHECKBOXES_SELECTOR + ':checked').length;
            var add_or_remove = (num_checkboxes !== num_checked);
            $('.agree-btn').toggleClass('inactive', add_or_remove);
        };

        // Enable the I Agree button only if all checkboxes are checked.

        enable_disable_agree_button();

        $(CHECKBOXES_SELECTOR).click(function () {
            enable_disable_agree_button();
        });

    });
});
