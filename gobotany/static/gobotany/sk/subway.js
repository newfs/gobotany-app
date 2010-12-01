// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, dijit, gobotany */

dojo.provide('gobotany.sk.subway');

dojo.require('dojox.embed.Flash');
dojo.require('dojox.data.JsonRestStore');

gobotany.sk.subway.click_more = function(event) {
    event.preventDefault();
    dojo.query('#subway ul ul').style('visibility', 'hidden');
    var this_ul = dojo.query(event.target.parentNode).query('ul');
    dojo.query(this_ul).style('visibility', 'visible');
};

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
};

gobotany.sk.subway.get_api_path = function(pile_group, pile) {
    // Return the API URL path for the pile group or pile.
    var api_path = '/';
    
    if (pile !== '') {
        api_path += 'piles/' + pile + '/';
    }
    else {
        api_path += 'pilegroups/' + pile_group + '/';
    }
    
    return api_path;
};

gobotany.sk.subway.embed_video = function(api_path) {
    var store = new dojox.data.JsonRestStore({target: api_path});
    store.fetch({
        onComplete: function(item) {
            var youtube_id = item.youtube_id;
            var video_url;
            if (youtube_id !== null) {
                video_url = 'http://www.youtube.com/v/' + youtube_id +
                            '?enablejsapi=1&version=3';
            }
            var node = dojo.query('#clip')[0];
            dojox.embed.Flash({path: video_url, width: 400, height: 400},
                              node);
        }
    });
};

gobotany.sk.subway.show_video = function(link_title, url) {
    // Populate a video popup with the video clip for the pile group or pile.
    dojo.query('#video_title')[0].innerHTML = link_title;

    var pile_group = '';
    var pile = '';
    var parts = url.split('/');
    if (parts.length) {
        if (parts[4] !== null) {
            pile_group = parts[4];
        }
        if (parts[5] !== null) {
            pile = parts[5];
        }
    }
    var api_path = gobotany.sk.subway.get_api_path(pile_group, pile);
    gobotany.sk.subway.embed_video(api_path);
};
