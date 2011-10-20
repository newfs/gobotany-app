/*
 * Code for special handling of full plant photos.
 */
dojo.provide('gobotany.sk.photo');

dojo.declare('gobotany.sk.photo.PhotoHelper', null, {

    constructor: function() {
    },

    prepare_to_enlarge: function() {
        // Do a few things before enlarging the photo on the screen.
        // Intended to be called using the Shadowbox onOpen handler.

        var title_element = dojo.query('#sb-title-inner')[0];
                                                    
        // Temporarily hide the title element.
        dojo.addClass(title_element, 'hidden');

        // Call a function to move the close link because an existing
        // onOpen handler with this function call is being overridden here.
        global_moveShadowboxCloseLink();
    },

    process_title_and_credit: function() {
        // Format the title text for a better presentation atop the photo.
        // Intended to be called using the Shadowbox onFinish handler.

        var title_element = dojo.query('#sb-title-inner')[0];
        var title_text = title_element.innerHTML;

        // Parse and mark up the title text.
        var parts = title_text.split('.');

        var image_type = parts[0].split(':')[0];
        // Get the properly-italicized scientific name from the page heading.
        var name = dojo.query('h2 .scientific')[0].innerHTML;
        var title = image_type + ': ' + dojo.trim(name) + '.';

        var html = title + '<br><span>' + parts[1] + '.' + parts[2] + '.' +
            parts[3] + '.</span>';
        title_element.innerHTML = html;

        // Show the title element again.
        dojo.removeClass(title_element, 'hidden');
    }

});
