// Google maps API via AMD: http://jasonwyatt.tumblr.com/post/18015760792/
(function () { 
    var callback = function () {},
        callbackName = 'gmapscallback' + (new Date()).getTime();
    window[callbackName] = callback;
    define(['//maps.googleapis.com/maps/api/js?key=AIzaSyBKPZHo9d81hL2cP_pR3uR57AUhbn6MxkM&callback=' +
            callbackName], function () {
        return google.maps;
    });
})();
