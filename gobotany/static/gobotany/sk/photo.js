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
        
        // Please see notes in activate_image_gallery.js.
        console.log('inside prepare_to_enlarge');

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

        // Please see notes in activate_image_gallery.js.
        console.log('inside process_title_and_credit');

        var title_element = dojo.query('#sb-title-inner')[0];
        var title_text = title_element.innerHTML;

        // Parse and mark up the title text.
        var parts = title_text.split('.');

        var title_parts = parts[0].split(':');
        var image_type = title_parts[0];
        var title = image_type;
        var name = '';
        // Get the properly-italicized scientific name from the page heading,
        // if available. (This is available on the species page.)
        // TODO: Replace with a function to properly italicize any
        // scientific name.
        var scientific_name = dojo.query('h2 .scientific');
        if (scientific_name.length > 0) {
            name = scientific_name[0].innerHTML;
        }
        else {
            name = '<i>' + dojo.trim(title_parts[1]) + '</i>';
        }
        if (name.length > 0) {
            title += ': ' + dojo.trim(name);
        }
        title += '.';

        var html = title + '<br><span>' + parts[1] + '.' + parts[2] + '.' +
            parts[3] + '.</span>';
        title_element.innerHTML = html;

        // Show the title element again.
        dojo.removeClass(title_element, 'hidden');
    }

});
