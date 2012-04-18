var requirejs = require('requirejs');
requirejs.config({baseUrl: 'scripts'});

var Filter = requirejs('simplekey/Filter');
var sample_choices = [
    {choice: 'red', taxa: [2, 3, 4]},
    {choice: 'orange', taxa: [2, 9, 10]},
    {choice: 'yellow', taxa: [4, 7]},
    {choice: 'blue', taxa: [8]}
];
var sample_lengths = [
    {min: 0, max: 2, taxa: [1]},
    {min: 1, max: 8, taxa: [2]},
    {min: 2, max: 5, taxa: [3, 4]},
    {min: 3, max: 6, taxa: [5]},
    {min: 9, max: 10, taxa: [6, 9, 10]}
];
var sample_choice_filter = function() {
    var f = new Filter({short_name: 'flower_color', value_type: 'TEXT'});
    f.install_values({
        pile_taxa: [2, 3, 4, 5, 6, 7],
        values: sample_choices
    });
    return f;
};
var sample_length_filter = function() {
    var f = new Filter({short_name: 'stem_length', value_type: 'LENGTH'});
    f.install_values({
        pile_taxa: [2, 3, 4, 5, 6, 7],
        values: sample_lengths
    });
    return f;
};

module.exports = {
    'Filter': {
        'knows its slug': function() {
            var f = new Filter({short_name: 'stem_length'});
            f.slug.should.equal('stem_length');
        },
        'only keeps choices that have taxa in the current pile': function() {
            var f = sample_choice_filter();
            f.values.length.should.equal(3);
            _.keys(f.choicemap).should.eql(['red', 'orange', 'yellow']);
        },
        'only keeps lengths that have taxa in the current pile': function() {
            var f = sample_length_filter();
            f.values.length.should.equal(4);
        },
        'keeps the choicemap empty when given length values': function() {
            var f = sample_length_filter();
            _.keys(f.choicemap).length.should.equal(0);
        },
        'knows which taxa in the pile have no value': function() {
            var f = sample_choice_filter();
            f.valueless_taxa.should.eql([5, 6]);
            var f = sample_length_filter();
            f.valueless_taxa.should.eql([7]);
        },
        'can filter by choice': function() {
            var f = sample_choice_filter();
            f.taxa_matching('red').should.eql([2, 3, 4]);
        },
        'when filtering by choice returns only in-pile taxa': function() {
            var f = sample_choice_filter();
            f.taxa_matching('orange').should.eql([2]);
        },
        'can filter by length': function() {
            var f = sample_length_filter();
            f.taxa_matching(3).should.eql([2, 3, 4, 5]);
        },
        'when filtering by length returns only in-pile taxa': function() {
            var f = sample_length_filter();
            f.taxa_matching(10).should.eql([6]);
        },
        'can return the length range that matches one taxon': function() {
            var f = sample_length_filter();
            f.allowed_ranges([2]).should.eql([{min: 1, max: 8}]);
        },
        'can return a combined range for several taxa': function() {
            var f = sample_length_filter();
            f.allowed_ranges([2, 3, 5]).should.eql([{min: 1, max: 8}]);
        },
        'can return disjoint ranges for several taxa': function() {
            var f = sample_length_filter();
            f.allowed_ranges([3, 5, 6]).should.eql([{min: 2, max: 6},
                                                    {min: 9, max: 10}]);
        }
    }
};
