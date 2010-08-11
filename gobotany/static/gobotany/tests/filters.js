dojo.provide('gobotany.tests.filters');
dojo.require('gobotany.filters');

/* Suggested naming convention for tests:
   First state a responsibility of the object. Then derive the test name from
   the responsibility, beginning with test_. Example:

   A MultipleChoiceFilter starts with no values.

   test_starts_with_no_values()
*/

doh.register('gobotany.tests.core.TestFilter', [
    function test_has_base_values() {
        var f = new gobotany.filters.Filter({friendly_name: 'f. name', order: 3,
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
    function test_starts_with_no_default_filters() {
        var fm = new gobotany.filters.FilterManager({pile_slug: 'foo'});
        doh.assertEqual([], fm.default_filters);
    },
    function test_loading_default_filters() {
        var fm = new gobotany.filters.FilterManager({pile_slug: 'foo'});

        // mock the store so we don't have to make network connections
        fm.store = {
            fetchItemByIdentity: function(args) { 
                console.warn(args);
                dojo.hitch(args.scope, args.onItem)({default_filters: [{}]});
            }
        };
        fm.load_default_filters();

        doh.assertEqual(fm.filters_loading, 1);
    }
]);
