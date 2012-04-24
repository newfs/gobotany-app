/* Tests for simplekey/ResultsPageState.js */

var requirejs = require('requirejs');
var ResultsPageState = requirejs('simplekey/ResultsPageState');

var sample_hash = '#_filters=family,genus,habitat_general,' +
    'state_distribution,trophophyll_form_ly,sporophyll_position_ly,' +
    'upright_shoot_form_ly,horizontal_shoot_position_ly,' +
    'trophophyll_morphology_ly,trophophyll_margins_ly' +
    '&family=Lycopodiaceae&trophophyll_form_ly=short%20and%20scale-like' +
    '&horizontal_shoot_position_ly=on%20the%20surface%20of%20the%20ground' +
    '&_visible=habitat_general&_view=photos&_show=branches';

var results_page_state = ResultsPageState.create({hash: sample_hash});

module.exports = {
    'ResultsPageState': {
        'can set hash': function () {
            results_page_state.hash.should.equal(sample_hash);
        },

        'can detect filters parameter in hash': function () {
            var has_filters = results_page_state.hash_has_filters();
            has_filters.should.equal(true);
        },

        'can parse a list of filters from the hash': function () {
            var filters = results_page_state.filters_from_hash();
            filters.length.should.be.above(0);
            filters.should.eql(
                ['family', 'genus', 'habitat_general', 'state_distribution',
                 'trophophyll_form_ly', 'sporophyll_position_ly',
                 'upright_shoot_form_ly', 'horizontal_shoot_position_ly',
                 'trophophyll_morphology_ly', 'trophophyll_margins_ly']);
        },

    }
};
