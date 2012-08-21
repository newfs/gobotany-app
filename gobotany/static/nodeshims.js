var requirejs = require('requirejs');
requirejs.config({
    baseUrl: 'scripts',
    nodeRequire: require
});

/* Use Node's jquery rather than the full-fledged library. */

requirejs.define('bridge/jquery', [], function() {
    require('jquery');
});

/* Replace our own "ember.js" loader with a subset of ember that is
   available under and can run on node.js: */

requirejs.define('bridge/ember', [
    'jsdom',
    /* Per https://github.com/emberjs/ember.js/pull/771#issuecomment-5701705
       we are using the "-node" versions of these packages for now instead
       of the main ones. */
    'ember-metal-node',
    'ember-runtime-node'
], function(jsdom) {
    jsdom.env({
        html: '<html><body></body></html>'
    }, function(err, window_) {
        window = window_;
    });
    return Ember;
});
