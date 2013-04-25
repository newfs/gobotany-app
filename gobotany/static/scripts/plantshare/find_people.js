define([
    'bridge/jquery'
], function ($) {

    $(document).ready(function () {
        var FORM_SELECTOR = '#find-people-form';
        $(FORM_SELECTOR + ' input[type=button]').click(function () {
            $(FORM_SELECTOR).submit();
        });
    });
});
