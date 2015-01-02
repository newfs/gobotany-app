// Go Botany Admin: customizations

// Django assigns jQuery's $ to django.jQuery
django.jQuery(document).ready(function () {

    // Pagination: Go To Page customization (see pagination.html):

    django.jQuery('#go-to-page-number').bind('keypress', function (event) {
        if (event.keyCode === 13) {
            django.jQuery('#go-to-page-button').trigger('click');
            return false;
        }
    });
    django.jQuery('#go-to-page-button').bind('click', function () {
        var url = window.location.href;
        var page = django.jQuery('#go-to-page-number').val();
        window.location.href = url.split('?')[0] + '?p=' + (page - 1);
        return false;
    });

});

