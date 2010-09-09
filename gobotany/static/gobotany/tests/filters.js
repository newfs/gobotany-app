dojo.provide('gobotany.tests.filters');
dojo.require('gobotany.filters');

/* Suggested naming convention for tests:
   First state a responsibility of the object. Then derive the test name from
   the responsibility, beginning with test_. Example:

   A MultipleChoiceFilter starts with no values.

   test_starts_with_no_values()
*/

doh.register('gobotany.tests.core.TestFilter', [
    function test_has_common_properties() {
        var f = new gobotany.filters.Filter(
            {friendly_name: 'f. name', order: 3,
             pile_slug: 'p. slug', value_type: 'text'});
        doh.assertEqual('f. name', f.friendly_name);
        doh.assertEqual('p. slug', f.pile_slug);
        doh.assertEqual(3, f.order);
        doh.assertEqual('text', f.value_type);
    },
]);

doh.register('gobotany.tests.core.TestMultipleChoiceFilter', [
    function test_has_character_short_name() {
        var f = new gobotany.filters.MultipleChoiceFilter(
            {friendly_name: 'f. name', order: 3, pile_slug: 'p. slug',
             value_type: 'text', character_short_name: 'c. name'});
        doh.assertEqual('f. name', f.friendly_name);
        doh.assertEqual('p. slug', f.pile_slug);
        doh.assertEqual(3, f.order);
        doh.assertEqual('text', f.value_type);
        doh.assertEqual('c. name', f.character_short_name);
    },
    function test_starts_with_no_values() {
        var f = new gobotany.filters.MultipleChoiceFilter(
            {friendly_name: 'f. name', order: 3, pile_slug: 'p. slug',
             value_type: 'text', character_short_name: 'c. name'});
        doh.assertEqual([], f.values);
    },
    function test_adds_values_to_collection() {
        var f = new gobotany.filters.MultipleChoiceFilter(
            {friendly_name: 'f. name', order: 3, pile_slug: 'p. slug',
             value_type: 'text', character_short_name: 'c. name'});
        var value1 = {'value': 'value1', 'count': 2};
        var value2 = {'value': 'value2', 'count': 4};
        var value3 = {'value': 'value3', 'count': 1};
        f.process_value(value1);
        f.process_value(value2);
        f.process_value(value3);
        doh.assertEqual(3, f.values.length);
    },
]);

doh.register('gobotany.tests.core.TestFilterManager', [
    function test_has_pile_slug() {
        var fm = new gobotany.filters.FilterManager({pile_slug: 'foo'});
        doh.assertEqual('foo', fm.pile_slug);
    },
    function test_starts_with_no_filters() {
        var fm = new gobotany.filters.FilterManager({pile_slug: 'foo'});
        doh.assertEqual([], fm.filters);
    },
    function test_can_load_pile_info() {
        var fm = new gobotany.filters.FilterManager(
                 {pile_slug: 'foo'});

        // mock the store so we don't have to make network connections
        fm.store = {
            fetchItemByIdentity: function(args) { 
                console.warn(args);
                // Pass a multiple-choice filter (value_type: TEXT) so
                // the filters_loading will be set as expected. However,
                // at a deeper level the code still tries to call out to
                // the network in order to grab filter values (see console).
                // (Verified that it did this before my 12 Aug changes. -JG)
                dojo.hitch(args.scope, args.onItem)({
                    default_filters: [{'value_type': 'TEXT'}]});
            }
        };
        fm.load_pile_info();

        doh.assertEqual(1, fm.filters_loading);
    },
    function test_can_add_text_filters() {
        var fm = new gobotany.filters.FilterManager({pile_slug: 'foo'});
        fm.add_text_filters(['foo', 'bar']);
        doh.assertEqual(2, fm.filters.length);
    },
    function test_can_set_selected_value_for_a_filter() {
        var fm = new gobotany.filters.FilterManager({pile_slug: 'foo'});
        fm.add_filter({filter_json: {'character_short_name': 'bar'}});
        fm.set_selected_value('bar', 'val');
        doh.assertEqual('val', fm.filters[0].selected_value);
    },
    function test_can_get_selected_value_for_a_filter() {
        var fm = new gobotany.filters.FilterManager({pile_slug: 'foo'});
        fm.add_filter({filter_json: {'character_short_name': 'bar'}});
        fm.set_selected_value('bar', 'val');
        doh.assertEqual('val', fm.get_selected_value('bar'));
    },
]);
