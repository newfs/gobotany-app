// 100% Height for Sidebar
function sidebarHeight() {
    var currentHeight = $('div#main').height();
    $('div#sidebar').css('height', currentHeight);
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