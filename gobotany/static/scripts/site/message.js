// Temporary: message banner

function getCookieValue(a) {   // https://stackoverflow.com/questions/5639346
    var b = document.cookie.match('(^|;)\\s*' + a + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
}

function hideMessageBanner() {
    document.getElementById('top-message').style.display = 'none';

    // Reposition the top of the search-suggest menu, initially set on page load.
    var elements = document.getElementsByClassName('suggester-menu');
    var menuElement = elements[0];
    if (menuElement) {
        menuElement.style.top = '103px';
    }

    // For species pages, make an adjustment to the maps positioning.
    var mapsElement = document.getElementById('maps');
    if (mapsElement) {
        mapsElement.style.top = '120px';
    }
}

// Hide the message banner if the cookie is still set.
if (getCookieValue('msg') === 'hide') {
    hideMessageBanner();
}
else {
    // For species pages, make an adjustment to the maps positioning.
    var mapsElement = document.getElementById('maps');
    if (mapsElement) {
        mapsElement.style.top = '186px';
    }
}

function closeMessageBanner() {
    // Hide the message banner for a while.
    var MINUTES_TO_HIDE = 30;
    var date = new Date();
    date.setTime(date.getTime() + MINUTES_TO_HIDE * 60 * 1000);
    document.cookie = 'msg=hide; expires=' + date.toGMTString() + '; path=/';
    hideMessageBanner();
}