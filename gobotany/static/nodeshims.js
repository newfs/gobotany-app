var requirejs = require('requirejs');
requirejs.config({baseUrl: 'scripts'});

/* Replace our own "ember.js" loader with a subset of ember that is
   available under and can run on node.js: */

requirejs.define('ember', [
    'ember-metal',
    'ember-runtime',
    'jsdom'
], function(x, Ember, jsdom) {
    jsdom.env({
        html: '<html><body></body></html>'
    }, function(err, window_) {
        window = window_;
    });
    return Ember;
});
