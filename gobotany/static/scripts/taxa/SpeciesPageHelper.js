/*
 * Code for adding behavior to species pages.
 */
define([
    'bridge/jquery',
    'bridge/shadowbox',
    'util/PhotoHelper',
    'util/glossarizer'
], function($, Shadowbox, PhotoHelper, glossarizer) {
var SpeciesPageHelper = {

    init: function() {
        this.photo_helper = PhotoHelper();
    },

    set_active_main_navigation: function() {
        // Set the active main navigation based on the breadcrumb links.
        var key = 'dkey';
        var breadcrumb_text = $('#breadcrumb p').text();
        if (breadcrumb_text.indexOf('Simple Key') > -1) {
            key = 'simple';
        }
        else if (breadcrumb_text.indexOf('Full Key') > -1) {
            key = 'full';
        }
        $('body').addClass(key);
    },

    toggle_character_group: function() {
        // Set handlers for toggling a character group.
        $('ul.full-description li h5').toggle(function() {
            var $heading = $(this);
            $heading.siblings('div').show();
            $heading.css('background-image',
                'url("/static/images/icons/minus.png")');
            return false;
        }, function() {
            var $heading = $(this);
            $heading.siblings('div').hide();
            $heading.css('background-image',
                'url("/static/images/icons/plus.png")');
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
            return false;
        }, function() {
            $('ul.full-description').hide();
            $(this).text('Show ' + 
                $(this).text().substr($(this).text().indexOf(' ')));
            $(this).css('background-image',
                'url("/static/images/icons/plus.png")');
            return false;
        });
    },

    wire_up_image_links: function() {
        // Wire up each image link to a Shadowbox popup handler.
        var IMAGE_LINKS_CSS = '#species-images a';
        var that = this;
        $(IMAGE_LINKS_CSS).each(function(i, link) {
            $(link).click($.proxy(function(event) {
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
            }, this));
        });
    },

    wire_up_us_map_link: function() {
        // Because the map is in an <object> element, a transparent div
        // is needed to make it clickable. Make this div cover the link
        // that appears below the map, too, for one large clickable area.
        var transparent_div =
            $('#sidebar .section.namap div.trans').first();
        transparent_div.click($.proxy(function(event) {
            event.preventDefault();
            // Open the North America distribution map in a lightbox.
            var content_element =
                $('#sidebar .section.namap div').first();
            Shadowbox.open({
                content: content_element.html(),
                player: 'html',
                height: 582,
                width: 1000
            });
        }, this));
    },

    setup: function() {
        // Set the active main navigation state depending on which key
        // is shown in the breadcrumb trail.
        this.set_active_main_navigation();

        // Set the handlers for toggling the character sections.       
        this.toggle_characters_full_list();

        // Link glossary terms.
        var selectors = '#sidebar dd, #main p:not(.nogloss), ' +
            '#main li:not(.nogloss), #main dt, #main dd, #main th, #main td';
        glossarizer.glossarize($(selectors));

        // Make image gallery able to show larger images.
        this.wire_up_image_links();

        // Wire up the enlarge link on the U.S. map.
        this.wire_up_us_map_link();
    }
};

// Create a small factory method to return, which will act
// as a little instance factory and constructor, so the user
// can do as follows:
// var obj = MyClassName(something, somethingelse);
function factory() {
    var instance = Object.create(SpeciesPageHelper);
    instance.init();
    return instance;
}

return factory;

});
