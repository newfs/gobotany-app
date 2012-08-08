define([
    'bridge/jquery'
], function ($) {

    // Turn anchor elements that contain broken-apart email addresses
    // into regular links with 'mailto's and properly formatted addresses.

    var mailto = {};

    mailto._address_from_text = function (text) {
        var address = text.replace(/\s/g, '');
        address = address.replace('[at]', '@');
        address = address.replace('[dot]', '.');
        return address;
    };

    mailto.make_link = function (css_selector) {
        var elements = $(css_selector);
        elements.each(function () {
            var address = mailto._address_from_text($(this).text());
            $(this).text(address);
            $(this).attr('href', 'mailto:' + address);
        });
    };

    return mailto;
});
