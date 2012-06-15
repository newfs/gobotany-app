define([
    'bridge/jquery'
], function($) {
return {
    // Make the sidebar as tall as it can be.
    set_height: function() {
        // On small screens, skip sidebar resizing entirely.
        if ($(window).width() <= 600) {
            return;
        }

        var MINIMUM_HEIGHT = 550;
        var new_height = 0;

        var main_height = $('div#main').height();
        if (main_height > new_height) {
            new_height = main_height;
        }

        // Handle cases where the sidebar is taller than the main content.
        // Because the sidebar is usually set to a static height when the
        // page loads, its height cannot be trusted as accurate (hence this
        // function). So, tally the heights of all the items in the sidebar.
        var SIDEBAR_SECTION_VERTICAL_PAD = 16;
        var sidebar_child_nodes = $('div#sidebar').children();
        var sidebar_contents_height = 0;
        for (var i = 0; i < sidebar_child_nodes.length; i++) {
            var section_height = $(sidebar_child_nodes[i]).height() +
                SIDEBAR_SECTION_VERTICAL_PAD;
            sidebar_contents_height += section_height;
        }
        if (sidebar_contents_height > new_height) {
            new_height = sidebar_contents_height;
        }

        if (new_height < MINIMUM_HEIGHT) {
            new_height = MINIMUM_HEIGHT;
        }

        $('div#sidebar').css('height', new_height);
    },

    setup: function() {
        that = this;
        $(document).ready(function() {
            // Set the initial sidebar height.
            that.set_height();
            $('#main img').load(function() {
                // Each time an image loads, the page gets taller.
                that.set_height();
            });
        });
    }
}
});
