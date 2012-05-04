/* Code for allowing the Google Chrome frame installation message on
 * Internet Explorer to be dismissed. This was requested because some
 * users reported problems with installing the plug-in. It was desired
 * to allow the option of viewing without the plug-in, even though things
 * may not work without it. */

function get_cookie(name) {
    var search = name + '=';
    var cookie_value = '';
    if (document.cookie.length > 0) {
        var start = document.cookie.indexOf(search);
        if (start !== -1) { 
            start += search.length;
            var end = document.cookie.indexOf(';', start);
            if (end === -1) {
                end = document.cookie.length;
            }
            cookie_value = unescape(document.cookie.substring(start, end));
        }
    }
    return cookie_value;
}

function dismiss_gcf_install() {
    // (Assume jQuery is loaded.)
    
    // Hide the installation elements.
    $('#ie-note').hide();
    $('.chromeFrameInstallDefaultStyle').hide();

    // Set a cookie that will expire when the browser session does,
    // to be used for deciding whether to show or hide the installation
    // message. On subsequent visits in a new browser session, the
    // installation message will be shown again.
    document.cookie = 'hide_gcf_install=true';
}
