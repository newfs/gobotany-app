var requirejs = require('requirejs');
var FilterController = requirejs('simplekey/FilterController');

var sample_filtercontroller = function() {
    var data = require('../testdata/taxa.js');
    return FilterController.create({taxadata: data.lycophytes});
};

module.exports = {
    'FilterController': {
        'builds its own family and genus filters': function() {
            var f = sample_filtercontroller();
            f.get('length').should.equal(2);
            _.keys(f.filtermap).length.should.equal(2);

            f.filtermap.family.slug.should.equal('family');
            f.filtermap.family.values.length.should.equal(4);
            f.filtermap.family.taxa_matching('Huperziaceae')
                .length.should.equal(2);

            f.filtermap.genus.slug.should.equal('genus');
            f.filtermap.genus.values.length.should.equal(8);
            f.filtermap.genus.taxa_matching('Isoetes')
                .length.should.equal(3);
        },
        'returns the whole pile when no filters are active': function() {
            var f = sample_filtercontroller();
            f.taxa.should.eql([
                85, 150, 880, 928, 1216, 1254, 1305, 1332, 1598, 1771,
                1907, 2123, 2555, 2720, 2839, 3062, 3257, 3321
            ]);
        },
        'can filter by family': function() {
            var f = sample_filtercontroller();
            f.get('filtermap').family.set('value', 'Huperziaceae');
            f.update();  // TODO: why can't this fire automatically?
            // Ember.run.sync();  and why doesn't this do the update?
            f.taxa.should.eql([1907, 3321]);
        }
    }
};
