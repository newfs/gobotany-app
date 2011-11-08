/*
 * Code for adding behavior to species pages.
 */
dojo.provide('gobotany.sk.species');

dojo.require('dojo.cookie');

dojo.require('gobotany.sk.glossary');
dojo.require('gobotany.sk.photo');
dojo.require('gobotany.utils');

dojo.declare('gobotany.sk.species.SpeciesPageHelper', null, {

    constructor: function() {
        this.glossarizer = gobotany.sk.glossary.Glossarizer();
        this.photo_helper = gobotany.sk.photo.PhotoHelper();
    },

    toggle_character_group: function() {
        // Set handlers for toggling a character group.
        // (Uses jQuery for historical reasons.)
        $('ul.full-description li').toggle(function(){
            $(this).children('ul').show();
            $(this).children('h5').css('background-image',
                'url("/static/images/icons/minus.png")');
            global_setSidebarHeight(); // TODO: remove global.js
            return false;
        }, function() {
            $(this).children('ul').hide();
            $(this).children('h5').css('background-image',
                'url("/static/images/icons/plus.png")');
            global_setSidebarHeight(); // TODO: remove global.js
            return false;
        });                
    },

    toggle_characters_full_list: function() {
        // Set handlers for toggling the full characteristics list.
        // (Uses jQuery for historical reasons.)
        var that = this;
        $('a.description-control').toggle(function(){
            $('ul.full-description').show();
            $(this).text('Hide Full Description');
            $(this).css('background-image',
                'url("/static/images/icons/minus.png")');
            that.toggle_character_group();
            global_setSidebarHeight(); // TODO: remove global.js
            return false;
        }, function() {
            $('ul.full-description').hide();
            $(this).text('Show Full Description');
            $(this).css('background-image',
                'url("/static/images/icons/plus.png")');
            global_setSidebarHeight(); // TODO: remove global.js
            return false;
        });
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
                        onOpen: that.photo_helper.prepare_to_enlarge,
                        onFinish: that.photo_helper.process_title_and_credit
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

    wire_up_us_map_link: function() {
        // Because the map is in an <object> element, a transparent div
        // is needed to make it clickable. Make this div cover the link
        // that appears below the map, too, for one large clickable area.
        var transparent_div =
            dojo.query('#sidebar .section.usmap div.trans')[0];
        dojo.connect(transparent_div, 'onclick', this, function(event) {
            event.preventDefault();
            // Open the U.S. distribution map in a lightbox.
            var content_element =
                dojo.query('#sidebar .section.usmap div')[0];
            Shadowbox.open({
                content: content_element.innerHTML,
                player: 'html',
                height: 490,
                width: 748
            });
        });
    },

    setup: function() {
        this.toggle_characters_full_list();

        // Highlight glossary terms where appropriate throughout the page.
        var that = this;
        var selectors = '#sidebar dd, #main p:not(.nogloss), #main li, ' +
                        '#main th, #main td';
        dojo.query(selectors).forEach(function(node) {
            that.glossarizer.markup(node);
        });

        // Make image gallery able to show larger images.
        this.wire_up_image_links();
        this.add_image_frame_handler();

        // Wire up the enlarge link on the U.S. map.
        this.wire_up_us_map_link();
    }
});
