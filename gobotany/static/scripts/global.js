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

// Show Working Area when sidebar options are selected
$(function() {
    // Set sidebar height
    sidebarHeight();

    // Hide Working Area
    $('div.working-area').hide();
    
    // Clicking Close button in working area
    $('div.working-area a.close').click(function(){
        $(this).parent().slideUp('fast', function(){
            sidebarHeight();
        });
        $('.option-list li').removeClass('active');
        return false;
    });
});

// Show/Hide for questions on Getting Started page
function global_toggleQuestions() {
    $('.question h4').toggle(function(){
        $(this).parent().find('li.hidden, a.screenshot').show();
        $(this).css('background-image','url("/static/images/icons/minus.png")');
        sidebarHeight();
        $(this).parent().find('a.show').text('Less...');
        return false;
    }, function() {
        $(this).parent().find('li.hidden, a.screenshot').hide();
        $(this).css('background-image','url("/static/images/icons/plus.png")');
        $(this).parent().find('a.show').text('More...');
        sidebarHeight();
        return false;
    });
    
    $('a.show').toggle(function() {
        $(this).parent().parent().parent().find(
            'li.hidden, a.screenshot').show();
        $(this).parent().parent().parent().find('h4').css('background-image',
            'url("/static/images/icons/minus.png")');
        sidebarHeight();
        $(this).text('Less...');
        return false;
    }, function() {
        $(this).parent().parent().parent().find(
            'li.hidden, a.screenshot').hide();
        $(this).parent().parent().parent().find('h4').css('background-image',
            'url("/static/images/icons/plus.png")');
        sidebarHeight();
        $(this).text('More...');
        return false;
    });
}

// Show/Hide for showing the whole list of characteristics on the Taxon page
function global_toggleList() {
    $('a.description-control').toggle(function(){
        $('ul.full-description').show();
        $(this).text('Hide Full Description');
        $(this).css('background-image',
            'url("/static/images/icons/minus.png")');
        global_toggleInfo();
        sidebarHeight();
        return false;
    }, function() {
        $('ul.full-description').hide();
        $(this).text('Show Full Description');
        $(this).css('background-image',
            'url("/static/images/icons/plus.png")');
        sidebarHeight();
        return false;
    });
}

//// Show/Hide for Characteristic List on Taxon page
function global_toggleInfo() {
    $('ul.full-description li').toggle(function(){
        $(this).children('ul').show();
        $(this).children('h5').css('background-image',
            'url("/static/images/icons/minus.png")');
        sidebarHeight();
        return false;
    }, function() {
        $(this).children('ul').hide();
        $(this).children('h5').css('background-image',
            'url("/static/images/icons/plus.png")');
        sidebarHeight();
        return false;
    }); 
}
