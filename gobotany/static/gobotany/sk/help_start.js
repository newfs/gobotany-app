// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, gobotany */

dojo.provide('gobotany.sk.help_start');

dojo.require('dojo.cookie');
dojo.require('dojox.embed.Flash');

var SKIP_PAGE_COOKIE_NAME = 'skip_help_start';

function embed_video_player() {
    var node = dojo.query('#clip')[0];
    var path = dojo.attr(dojo.query('> a', node)[0], 'href');
    var player = new dojox.embed.Flash({path: path,
                                        width: 250,
                                        height: 250}, node);
}

function set_skip_page_checkbox(checkbox) {
    var cookie_value = dojo.cookie(SKIP_PAGE_COOKIE_NAME);
    checkbox.checked = (cookie_value == 'y');
}

function set_skip_page_cookie() {
    var DAYS_UNTIL_COOKIE_EXPIRES = 10000;
    var cookie_value = 'n';
    if (this.checked) {
        cookie_value = 'y';
    }
    dojo.cookie(SKIP_PAGE_COOKIE_NAME, cookie_value,
        {path: '/', expires: DAYS_UNTIL_COOKIE_EXPIRES});
}

function set_up_skip_checkbox() {
    // Set up the checkbox that allows skipping this Getting Started
    // help page when starting a new plant identification session.

    // Wire up a checkbox handler that changes the cookie value.
    var checkbox = dojo.query('#skip-page')[0];
    dojo.connect(checkbox, 'onchange', null, set_skip_page_cookie);

    // Set the checkbox state from the current cookie value.
    set_skip_page_checkbox(checkbox);
}

gobotany.sk.help_start.init = function() {
    embed_video_player();
    set_up_skip_checkbox();
}