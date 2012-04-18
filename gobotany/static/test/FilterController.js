var requirejs = require('requirejs');
var FilterController = requirejs('simplekey/FilterController');

var sample_filtercontroller = function() {
    var data = require('../testdata/taxa.js');
    return new FilterController({base_vector: data.base_vector,
                                 taxadata: data.lycophytes});
};

module.exports = {
    'FilterController': {
        'builds its own family and genus filters': function() {
            var f = sample_filtercontroller();
            _.keys(f.filters).length.should.equal(2);

            f.filters.family.slug.should.equal('family');
            f.filters.family.values.length.should.equal(4);
            f.filters.family.taxa_matching('Huperziaceae')
                .length.should.equal(2);

            f.filters.genus.slug.should.equal('genus');
            f.filters.genus.values.length.should.equal(8);
            f.filters.genus.taxa_matching('Isoetes').length.should.equal(3);
        }
    }
};
