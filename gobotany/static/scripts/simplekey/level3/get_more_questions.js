define([
    'bridge/jquery',
    'bridge/underscore'
], function(
    $, _
) {
    exports = {};

    exports.install_handlers = function() {
        console.log('activate!');
    };

    return exports;
});
