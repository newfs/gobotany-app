// TODO: Integrate all this code into an appropriate place within the
// main JavaScript code base, and get rid of this file.

// 100% Height for Sidebar
function sidebarHeight() {
    var MINIMUM_HEIGHT = 550;
    var newHeight = 0;

    var mainHeight = $('div#main').height();
    if (mainHeight > newHeight) {
        newHeight = mainHeight;
    }

    // Handle cases where the sidebar is taller than the main content.
    // Because the sidebar is usually set to a static height when the
    // page loads, its height cannot be trusted as accurate (hence this
    // function). So, tally the heights of all the items in the sidebar.
    var SIDEBAR_SECTION_VERTICAL_PAD = 16;
    var sidebarChildNodes = $('div#sidebar').children();
    var sidebarContentsHeight = 0;
    for (var i = 0; i < sidebarChildNodes.length; i++) {
        var sectionHeight = $(sidebarChildNodes[i]).height() +
            SIDEBAR_SECTION_VERTICAL_PAD;
        sidebarContentsHeight += sectionHeight;
    }
    if (sidebarContentsHeight > newHeight) {
        newHeight = sidebarContentsHeight;
    }

    if (newHeight < MINIMUM_HEIGHT) {
        newHeight = MINIMUM_HEIGHT;
    }

    $('div#sidebar').css('height', newHeight);
}

// Wrapper for calling from elsewhere; make code in global.js easier to keep
// track of when called from the Dojo-based code.
function global_setSidebarHeight() {
    sidebarHeight();
}

// Show Working Area when sidebar options are selected.
// (Note: This code is applied to all pages upon loading.)
$(function() {
    // Set sidebar height
    sidebarHeight();

    // Clicking Close button in working area
    $('div.working-area a.close').click(function(){
        $(this).parent().slideUp('fast', function(){
            sidebarHeight();
        });
        $('.option-list li').removeClass('active');
        return false;
    });
});

// Animate and position the Shadowbox close link.
function global_moveShadowboxCloseLink() {
    var cb = document.getElementById('sb-nav-close');
    var tb = document.getElementById('sb-wrapper');
    if (tb) {
        tb.appendChild(cb);
    }
}

