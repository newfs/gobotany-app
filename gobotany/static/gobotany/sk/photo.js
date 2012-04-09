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

        // Call a function to do the usual Shadowbox initialization because
        // an existing onOpen handler with this function call is being
        // overridden here.
        shadowbox_on_open();
    },

    process_credit: function() {
        // Format the title text for a better presentation atop the photo.
        // Intended to be called using the Shadowbox onFinish handler.

        var title_element = dojo.query('#sb-title-inner')[0];
        var title_text = title_element.innerHTML;

        // Parse and mark up the title text.

        var parts = title_text.split(' ~ ');
        var image_title = parts[0];
        var copyright_holder = parts[1];
        var copyright = parts[2];
        var source = "";
        if (parts[3]) {
            source = parts[3];
        }

        var title_parts = image_title.split(':');
        var image_type = title_parts[0];
        var title = image_type;
        var name = '';
        // Get the properly-italicized scientific name from the page heading,
        // if available, such as on the species page. Otherwise, just
        // italicize the entire plant name portion of the title for now. This
        // will generally be correct for the groups and subgroups pages'
        // galleries, which tend not to show varieties, subspecies, etc.
        var scientific_name = dojo.query('h2 .scientific');
        if (scientific_name.length > 0) {
            name = dojo.trim(scientific_name[0].innerHTML) + '.';
        }
        else if (title_parts[1] !== undefined) {
            name = '<i>' + dojo.trim(title_parts[1]) + '</i>';
        }
        if (name.length > 0) {
            title += ': ' + name;
        }

        var html = '<div><h6>' + title + '</h6><span>' + copyright_holder +
            ' ' + copyright + ' <a href="/legal/terms-of-use/#ip" ' +
            'target="_blank">Terms of Use' + '</a></span>';
        if (source !== "") {
            html += '<br><span>' + parts[3] + '</span>';
        }
        html += '</div>';
        title_element.innerHTML = html;

        // Show the title element again.
        dojo.removeClass(title_element, 'hidden');
    }

});
