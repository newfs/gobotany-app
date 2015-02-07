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

    // Distribution records: Customize Save and Add Another by populating
    // the Scientific Name field with the name from the record just added.
    var just_added = false,
        message, scientific_name;
    if (django.jQuery('#content h1').text() === 'Add Distribution record') {
        // If a record was just added, use its scientific name again.
        message = django.jQuery('.messagelist .info').text();
        if (message.indexOf('was added successfully. ' +
                'You may add another Distribution record below') > -1) {
            just_added = true;
        }
        if (just_added) {
            scientific_name = message.split(':')[0].split('"')[1];
            django.jQuery('#id_scientific_name').val(scientific_name);
            django.jQuery('#id_state').focus();
        }
    }

    // Distribution records: for the Save and Edit Next button, modify
    // the record link URLs to pass all record ids for the current page.
    // These will be used to determine which record is the next one each
    // time the button is pressed.
    if (django.jQuery(
        '#content h1').text() === 'Select Distribution record to change') {

        var ids = [],
            url_parts, all_ids;

        // Get the list of all ids in sequence, for passing as a
        // request parameter value.
        django.jQuery('#result_list tbody th a').each(function () {
            url_parts = django.jQuery(this).attr('href').split('/');
            ids.push(url_parts[4]);
        });
        all_ids = ids.join(',');

        // Make another pass through all the links and append the
        // request parameter to each URL.
        django.jQuery('#result_list tbody th a').each(function () {
            url = django.jQuery(this).attr('href') + '?ids=' + all_ids;
            django.jQuery(this).attr('href', url);
        });
    }
});

