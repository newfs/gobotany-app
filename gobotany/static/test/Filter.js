var requirejs = require('requirejs');
requirejs.config({baseUrl: 'scripts'});

module.exports = {
    'Filter': {
        'should return a test value': function() {
            var f = requirejs('simplekey/Filter');
            f.should.equal('test value');
        }
    }
};
