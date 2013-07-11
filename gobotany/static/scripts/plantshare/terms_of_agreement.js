define([
    'bridge/jquery',
], function ($) {

    var CHECKBOXES_SELECTOR = '#main input[type="checkbox"]';
    var num_checkboxes = $(CHECKBOXES_SELECTOR).length;

    $(document).ready(function () {

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
