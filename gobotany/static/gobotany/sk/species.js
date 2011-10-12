/*
 * Code for adding behavior to species pages.
 */

dojo.provide('gobotany.sk.species');

dojo.require('dojo.cookie');

dojo.require('gobotany.sk.glossary');
dojo.require('gobotany.utils');

dojo.declare('gobotany.sk.species.SpeciesPageHelper', null, {

    constructor: function() {
        this.glossarizer = gobotany.sk.glossary.Glossarizer();
    },

    prepare_to_open_image: function() {
        var title_element = dojo.query('#sb-title-inner')[0];
                                                    
        // Temporarily hide the title element.
        dojo.addClass(title_element, 'hidden');

        // Call a function to move the close link because an existing
        // onOpen handler with this function call is being overridden here.
        global_moveShadowboxCloseLink();
    },

    process_photo_title_and_credit: function() {
        // Format the title text for a better presentation atop the photo.

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
    },

    wire_up_image_links: function() {
        // Wire up each image link to a Shadowbox popup handler.
        var IMAGE_LINKS_CSS = '#species-images .scrollableArea a';
        var that = this;
        dojo.query(IMAGE_LINKS_CSS).forEach(function(link) {
            dojo.connect(link, 'onclick', this, function(event) {
                // Prevent the regular link (href) from taking over.
                event.preventDefault();

                // Open the image.
                Shadowbox.open({
                    content: link.href,
                    player: 'img',
                    title: link.title,
                    options: {
                        onOpen: that.prepare_to_open_image,
                        onFinish: that.process_photo_title_and_credit
                    }
                });
            });
        });

    },

    add_image_frame_handler: function() {
        // Add a handler to the image frame in order to be able to activate
        // the Shadowbox popup for the image underneath it. Otherwise the
        // popup would not be available because the image frame layer
        // overlays it and blocks events, despite the image being visible.

        var image_frame = dojo.query('.img-gallery .frame')[0];
        dojo.connect(image_frame, 'onclick', this, function(event) {
            var POSITION_RELATIVE_TO_DOCUMENT_ROOT = true;
            var IMAGE_ON_SCREEN_MIN_PX = 200;
            var IMAGE_ON_SCREEN_MAX_PX = 900;
            var IMAGE_LINKS_CSS = '.img-container .images .single-img a';
            var image_links = dojo.query(IMAGE_LINKS_CSS);
            var i;
            for (i = 0; i < image_links.length; i++) {
                var position_info = dojo.position(image_links[i],
                    POSITION_RELATIVE_TO_DOCUMENT_ROOT);
                if (position_info.x >= IMAGE_ON_SCREEN_MIN_PX &&
                    position_info.x <= IMAGE_ON_SCREEN_MAX_PX) {

                    gobotany.utils.click_link(image_links[i]);
                    break;
                }
            }
        });
    },

    setup: function() {
        global_toggleList();

        // Highlight glossary terms where appropriate throughout the page.
        var that = this;
        dojo.query('#info p').forEach(function(node) {
            that.glossarizer.markup(node);
        });

        // Check for whether the stored filter-state cookie pertains to the
        // pile/results page for this plant. If so, replace the hyperlink href
        // for the pile/results page with the URL from the cookie in order to
        // persist filter state when the user clicks the link to go back.
        var last_plant_id_url = dojo.cookie('last_plant_id_url');
        if (last_plant_id_url !== undefined) {
            var url_parts = window.location.toString().split('/');
            var pile_results_url = url_parts.slice(0, 6).join('/'); 
            if (last_plant_id_url.indexOf(pile_results_url) !== -1) {
                var link = dojo.byId('results-link');
                dojo.attr(link, 'href', last_plant_id_url);
            }
        }

        // Decide whether to add a Go Back link based on whether the previous
        // URL was a pile/results page. If it was, add the link.
        var previous_url = '';
        if (document.referrer !== undefined) {
            previous_url = document.referrer;
        }

        // If the previous URL can be found as a substring in the current
        // species page URL, then the previous page was indeed a pile/results
        // page.
        if (previous_url.length > 0) {
            if (window.location.href.indexOf(previous_url) > -1) {
                var species_node = dojo.query('#species')[0];
                if (species_node) {
                    var back_link = dojo.create('a',
                        {innerHTML: '&lt; Back to plant identification'});
                    dojo.attr(back_link, 'class', 'back');
                    // The last plant identification URL should be the
                    // correct destination for the link.
                    dojo.attr(back_link, 'href', last_plant_id_url);
                    dojo.place(back_link, species_node);
                }
            }
        }

        // Make image gallery able to show larger images.
        this.wire_up_image_links();
        this.add_image_frame_handler();
    }
});
