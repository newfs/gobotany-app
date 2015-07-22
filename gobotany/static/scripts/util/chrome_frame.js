/* Code for allowing the browser upgrade message for Internet Explorer < 10
 * to be skipped for the current session, so the user can continue to use
 * parts of the site anyway. */

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
    // Hide the message.
    document.getElementById('ie-note').style.display = 'none';
    var elements = document.body.getElementsByTagName('iframe');
    for (var i = 0; i < elements.length; i++) {
        elements[i].style.display = 'none';
    }

    // Set a cookie that will expire when the browser session does,
    // to be used for deciding whether to show or hide the browser
    // version message. On subsequent visits in a new browser session,
    // the message will be shown again.
    document.cookie = 'hide_gcf_install=true;path=/';
}
