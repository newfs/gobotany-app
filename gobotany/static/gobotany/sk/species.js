/*
 * Code for adding behavior to species pages.
 */
define([
    'dojo/_base/declare',
    'dojo/_base/lang',
    'dojo/query',
    'dojo/on',
    'dojo/cookie',
    'dojo/dom-geometry',
    'bridge/jquery',
    'bridge/shadowbox',
    'gobotany/sk/photo',
    'gobotany/utils',
    'util/sidebar',
    'simplekey/glossarize'
], function(declare, lang, query, on, cookie, domGeom, $, Shadowbox,
    PhotoHelper, utils, sidebar, glossarize) {
return declare('gobotany.sk.species.SpeciesPageHelper', null, {

    constructor: function() {
        this.photo_helper = PhotoHelper();
    },

    toggle_character_group: function() {
        // Set handlers for toggling a character group.
        $('ul.full-description li h5').toggle(function() {
            $(this).siblings('div').show();
            $(this).css('background-image',
                'url("/static/images/icons/minus.png")');
            sidebar.set_height();
            return false;
        }, function() {
            $(this).siblings('div').hide();
            $(this).css('background-image',
                'url("/static/images/icons/plus.png")');
            sidebar.set_height();
            return false;
        });                
    },

    toggle_characters_full_list: function() {
        // Set handlers for toggling the full characteristics list.
        var that = this;
        $('a.description-control').toggle(function() {
            $('ul.full-description').show();
            $(this).text('Hide ' + 
                $(this).text().substr($(this).text().indexOf(' ')));
            $(this).css('background-image',
                'url("/static/images/icons/minus.png")');
            that.toggle_character_group();
            sidebar.set_height();
            return false;
        }, function() {
            $('ul.full-description').hide();
            $(this).text('Show ' + 
                $(this).text().substr($(this).text().indexOf(' ')));
            $(this).css('background-image',
                'url("/static/images/icons/plus.png")');
            sidebar.set_height();
            return false;
        });
    },

    wire_up_image_links: function() {
        // Wire up each image link to a Shadowbox popup handler.
        var IMAGE_LINKS_CSS = '#species-images a';
        var that = this;
        query(IMAGE_LINKS_CSS).forEach(function(link) {
            on(link, 'click', lang.hitch(this, function(event) {
                // Prevent the regular link (href) from taking over.
                event.preventDefault();

                // Open the image.
                Shadowbox.open({
                    content: link.href,
                    player: 'img',
                    title: link.title,
                    options: {
                        onOpen: that.photo_helper.prepare_to_enlarge,
                        onFinish: that.photo_helper.process_credit
                    }
                });
            }));
        });
    },

    wire_up_us_map_link: function() {
        // Because the map is in an <object> element, a transparent div
        // is needed to make it clickable. Make this div cover the link
        // that appears below the map, too, for one large clickable area.
        var transparent_div =
            query('#sidebar .section.namap div.trans')[0];
        on(transparent_div, 'click', lang.hitch(this, function(event) {
            event.preventDefault();
            // Open the North America distribution map in a lightbox.
            var content_element =
                query('#sidebar .section.namap div')[0];
            Shadowbox.open({
                content: content_element.innerHTML,
                player: 'html',
                height: 582,
                width: 1000
            });
        }));
    },

    setup: function() {
        this.toggle_characters_full_list();

        var selectors = '#sidebar dd, #main p:not(.nogloss), #main dt, ' +
            '#main dd, #main li, #main th, #main td';
        glossarize($(selectors));

        // Make image gallery able to show larger images.
        this.wire_up_image_links();

        // Wire up the enlarge link on the U.S. map.
        this.wire_up_us_map_link();
        sidebar.setup()
    }
});
});
