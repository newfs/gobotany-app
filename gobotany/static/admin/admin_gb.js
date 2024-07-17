// Go Botany Admin: customizations

// Django assigns jQuery's $ to django.jQuery, but in some cases
// it's not ready right away, so use a non-jQuery way to start.
document.addEventListener("DOMContentLoaded", function (event) {

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

    // D. Key: add custom navigation item
    django.jQuery('body.app-dkey .breadcrumbs').append(
        '<div class="dkey-custom"><a href="/edit/dkey/">D. Key Editor</div>');

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

    // ContentImage change screen: customize to allow picking
    // a taxon from a read-only select to populate object_id.

    if (document.querySelector("body.model-contentimage.change-form")) {
        let taxonLookup = document.querySelector(".taxon-lookup");
        if (taxonLookup) {
            taxonLookup.addEventListener("change", (event) => {
                let taxonId = event.target.value;
                if (taxonId > -1) {
                    let objectIdField = document.querySelector(
                        "input#id_object_id");
                    if (objectIdField) {
                        objectIdField.value = taxonId;
                    }
                }
            });
        }
    }
});