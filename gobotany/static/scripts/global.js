// 100% Height for Sidebar
function sidebarHeight() {
    var MINIMUM_HEIGHT = 850;

    var helpButton = $('div#sidebar a.get-help-btn');
    if (helpButton.length > 0) {
        var helpButtonTopPosition = helpButton.position().top;

        var headerHeight = $('header').height();

        var newHeight = helpButtonTopPosition - headerHeight;

        var mainHeight = $('div#main').height();
        if (mainHeight > newHeight) {
            newHeight = mainHeight;
        }

        if (newHeight < MINIMUM_HEIGHT) {
            newHeight = MINIMUM_HEIGHT;
        }

        $('div#sidebar').css('height', newHeight);
    }
}

// Wrapper for calling from elsewhere using a name that could be easier
// to keep track of
function _global_setSidebarHeight() {
    sidebarHeight();
}

// Show Working Area when sidebar options are selected
$(function() {
    // Set sidebar height
    sidebarHeight();

    // Hide Working Area
    $('div.working-area').hide();
    
    // Toggling sidebar options
    $('a.option').toggle(function(){
        $('div.working-area').slideDown('fast', function(){
            sidebarHeight();
        });
        $(this).parent().addClass('active');
        return false;
    }, function(){
        $('div.working-area').slideUp('fast', function(){
            sidebarHeight();
        });
        $(this).parent().removeClass('active');
        return false;
    });

    // Clicking Close button in working area
    $('div.working-area a.close').click(function(){
        $(this).parent().slideUp('fast', function(){
            sidebarHeight();
        });
        $('.option-list li').removeClass('active');
        return false;
    });
});