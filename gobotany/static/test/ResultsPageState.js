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
        'can have a hash': function () {
            var trimmed_sample_hash = sample_hash.substr(1);
            results_page_state.hash.should.equal(trimmed_sample_hash);
        },

        'can detect the filters parameter in the hash': function () {
            var has_filters = results_page_state.hash_has_filters();
            has_filters.should.equal(true);
        },

        'can parse a list of filters from the hash': function () {
            var filters = results_page_state.filters_from_hash();
            filters.length.should.be.above(0);
            filters.should.eql([
                'family', 'genus', 'habitat_general', 'state_distribution',
                'trophophyll_form_ly', 'sporophyll_position_ly',
                'upright_shoot_form_ly', 'horizontal_shoot_position_ly',
                'trophophyll_morphology_ly', 'trophophyll_margins_ly']);
        },

        'can parse filter values from the hash': function () {
            var filter_values = results_page_state.filter_values_from_hash();
            _.size(filter_values).should.be.above(0);
            filter_values.should.eql({
                'family': 'Lycopodiaceae',
                'trophophyll_form_ly': 'short%20and%20scale-like',
                'horizontal_shoot_position_ly':
                    'on%20the%20surface%20of%20the%20ground'});
        },

        'can parse the visible filter from the hash': function () {
            var visible_filter =
                results_page_state.parameter_from_hash('visible');
            visible_filter.should.equal('habitat_general');
        },

        'can parse the tab view from the hash': function () {
            var tab_view = results_page_state.parameter_from_hash('view');
            tab_view.should.equal('photos');
        },

        'can parse the photo type from the hash': function () {
            var photo_type = results_page_state.parameter_from_hash('show');
            photo_type.should.equal('branches');
        },
    }
};
