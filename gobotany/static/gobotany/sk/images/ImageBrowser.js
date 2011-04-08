// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, console */

dojo.provide('gobotany.sk.images.ImageBrowser');

// Class for helping create a browsable set of images on a page (such as in
// the plant preview popup, or the species page).

dojo.declare('gobotany.sk.images.ImageBrowser', null, {
    constructor: function() {
        this.images = [];
        this.css_selector = '';
        this.image_node = null;
        this.message_node = null;
        this.first_image_index = 0;
        this.url_key = 'url';  // Or, can set to 'scaled_url'
    },

    setup: function() {
        // Clear and reconstruct the navigation area so as not to keep
        // connecting more event handlers to the Previous and Next links
        // every time the user opens another popup.
        var navigation_node = dojo.query(this.css_selector + ' p.nav')[0];
        dojo.empty(navigation_node);
        var nav_html = '<a>&lt; prev</a> <span>? of ?</span><a>next &gt;</a>';
        dojo.attr(navigation_node, { innerHTML: nav_html });

        // Set some frequently used nodes as properties.
        var image_selector = this.css_selector + ' img';
        this.image_node = dojo.query(image_selector)[0];
        var message_selector = this.css_selector + ' span';
        this.message_node = dojo.query(message_selector)[0];

        // Clear the image and message.
        dojo.attr(this.image_node, 'src', '');
        dojo.attr(this.image_node, 'alt', 'not available');
        this.message_node.innerHTML = '';

        // Set whichever image is to be the first one shown.
        if (this.images.length > 0) {
            this.set_image(this.first_image_index);
        }

        this.set_navigation_links();
    },

    set_image: function(index) {
        // Set the image URL and alt text, and set the count message.
        dojo.attr(this.image_node, 'src', this.images[index][this.url_key]);
        dojo.attr(this.image_node, 'alt', this.images[index].title);
        this.message_node.innerHTML = (index + 1) + ' of ' +
            this.images.length;
    },

    set_navigation_links: function() {
        // Wire up the previous and next links, or hide them if not needed.
        var links = dojo.query(this.css_selector + ' a');
        for (var i = 0; i < links.length; i++) {
            if (this.images.length > 1) {
                dojo.removeClass(links[i], 'hidden');
                var change_image_function = this.previous_image;
                if (links[i].innerHTML.indexOf('next') > -1) {
                    change_image_function = this.next_image;
                }
                dojo.connect(links[i], 'onclick', this,
                    change_image_function);
            }
            else {
                dojo.addClass(links[i], 'hidden');
            }
        }

        // Display the navigation links and message.
        dojo.query(this.css_selector + ' .nav').style({
            'display': 'block' });
    },

    change_image: function(link_text) {
        var current_image_url = dojo.attr(this.image_node, 'src');

        // Get the index of the image that is showing.
        var current_image_index = this.get_current_image_index(
            current_image_url);
        if (current_image_index < 0) {
            console.error('ImageBrowser: current_image_index is ' +
                current_image_index + ' (should not be < 0)');
        }

        // Get the index of the image to show next.
        var new_image_index = this.get_new_image_index(current_image_index,
            link_text);

        // Change the image and update the count message.
        this.set_image(new_image_index);
    },

    previous_image: function() {
        this.change_image('prev');
    },

    next_image: function() {
        this.change_image('next');
    },

    get_current_image_index: function(current_image_url) {
        // Figure out which image is currently showing. The URL key is for
        // supporting URLs for different image sizes, i.e., full images or
        // thumbnails.
        var current_image_index = -1;
        var i = 0;
        while (current_image_index === -1 && i < this.images.length) {
            if (current_image_url === this.images[i][this.url_key]) {
                current_image_index = i;
            }
            i++;
        }

        return current_image_index;
    },

    get_new_image_index: function(current_image_index, link_text) {
        // Figure out which image to show next.
        var new_image_index = current_image_index;

        if (link_text.indexOf('next') >= 0) {
            new_image_index++;
        }
        else if (link_text.indexOf('prev') >= 0) {
            new_image_index--;
        }

        if (new_image_index < 0) {
            new_image_index = this.images.length - 1;
        }
        else if (new_image_index > this.images.length - 1) {
            new_image_index = 0;
        }

        return new_image_index;
    },

    get_first_image_index_of_type: function(image_type) {
        // Get the first image index of the specified type.
        var first_image_index = -1;
        var i = 0;
        while (first_image_index === -1 && i < this.images.length) {
            if (image_type === this.images[i].type) {
                first_image_index = i;
            }
            i++;
        }

        return first_image_index;
    }

});
