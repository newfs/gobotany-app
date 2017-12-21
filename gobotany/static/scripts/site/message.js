// temporary: message banner

function getCookieValue(a) {   // https://stackoverflow.com/questions/5639346
    var b = document.cookie.match('(^|;)\\s*' + a + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
}

function hideMessageBanner() {
    document.getElementById('top-message').style.display = 'none';

    // For species pages, make an adjustment to the maps positioning.
    var mapsElement = document.getElementById('maps');
    if (mapsElement) {
        mapsElement.style.top = '128px';
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
        mapsElement.style.top = '205px';
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