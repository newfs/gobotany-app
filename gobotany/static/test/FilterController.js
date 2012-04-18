var $ = require('jquery');
var requirejs = require('requirejs');

requirejs.config({baseUrl: 'scripts'});

module.exports = {
    'FilterController': {
        'should return a test value': function() {
            var f = requirejs('simplekey/FilterController');
            var g = $.Deferred();
            var d = f.add_filter('filtername', function(short_name) {
                return g;
            });
            g.resolve();
            f.testval.should.eql(2);
        }
    }
};
