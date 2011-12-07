// TODO: Integrate all this code into an appropriate place within the
// main JavaScript code base, and get rid of this file.

define(['jquery.tools.min'], function() {

// (Note: This code is applied to all pages upon loading.)
$(function() {
    // Clicking Close button in working area
    $('div.working-area a.close').click(function(){
        $(this).parent().slideUp('fast', function(){
            sidebar_set_height();
        });
        $('.option-list li').removeClass('active');
        return false;
    });
});

// Animate and position the Shadowbox close link.
global_moveShadowboxCloseLink = function() {
    var cb = document.getElementById('sb-nav-close');
    var tb = document.getElementById('sb-wrapper');
    if (tb) {
        tb.appendChild(cb);
    }
};

});
