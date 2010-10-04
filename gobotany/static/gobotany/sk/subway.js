dojo.provide('gobotany.sk.subway');

gobotany.sk.subway.click_more = function(event) {
    event.preventDefault();
    dojo.query('#subway ul ul').style('visibility', 'hidden');
    var this_ul = dojo.query(event.target.parentNode).query('ul');
    dojo.query(this_ul).style('visibility', 'visible');
}

gobotany.sk.subway.init = function(is_help_collections) {
    dojo.query('#subway li a.more').connect(
        'onclick', gobotany.sk.subway.click_more);

    if (is_help_collections) {
        // For the Help | Understanding Plant Collections page only,
        // add click events to bring up a popup dialog with a video clip
        // in place of each item's regular link href.
        dojo.query('#subway li a.video').forEach(function(link) {
            dojo.connect(link, 'onclick', function(event) {
                event.preventDefault();
                dijit.byId('video').show();
                gobotany.sk.subway.show_video(link.innerHTML,
                    dojo.attr(link, 'href'));
            });
        });
        
    }
}

gobotany.sk.subway.show_video = function(link_title, url) {
    // Populate a video popup with the video clip for the pile group or pile.
    //alert('url: ' + url);
    dojo.query('#video_title')[0].innerHTML = link_title;
    dojo.query('#video p')[0].innerHTML = url;
}