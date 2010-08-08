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
        var f = new Filter({friendly_name: 'f. name', order: 3,
                            pile_slug: 'p. slug', value_type: 'text'});
        doh.assertEqual('f. name', f.friendly_name);
        doh.assertEqual('p. slug', f.pile_slug);
        doh.assertEqual(3, f.order);
        doh.assertEqual('text', f.value_type);
    },
]);

doh.register('gobotany.tests.core.TestMultipleChoiceFilter', [
    function test_has_character_short_name() {
        var f = new MultipleChoiceFilter(
                    {friendly_name: 'f. name', order: 3, pile_slug: 'p. slug',
                     value_type: 'text', character_short_name: 'c. name'});
        doh.assertEqual('f. name', f.friendly_name);
        doh.assertEqual('p. slug', f.pile_slug);
        doh.assertEqual(3, f.order);
        doh.assertEqual('text', f.value_type);
        doh.assertEqual('c. name', f.character_short_name);
    },
    function test_starts_with_no_values() {
        var f = new MultipleChoiceFilter(
                    {friendly_name: 'f. name', order: 3, pile_slug: 'p. slug',
                     value_type: 'text', character_short_name: 'c. name'});
        doh.assertEqual([], f.values);
    },
    function test_adds_values_to_collection() {
        var f = new MultipleChoiceFilter(
                    {friendly_name: 'f. name', order: 3, pile_slug: 'p. slug',
                     value_type: 'text', character_short_name: 'c. name'});
        var value1 = {'value_str': 'value_str_1'};
        var value2 = {'value_str': 'value_str_2'};
        var value3 = {'value_str': 'value_str_3'};
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
    function test_loads_default_filters_if_they_exist() {
        // Sort of an integration test - do we want here?
        var fm = new gobotany.filters.FilterManager({pile_slug: 'lycophytes'});
        fm.load_default_filters();
        doh.assertTrue(fm.default_filters.length > 0);
    },
    function test_loads_no_default_filters_if_none_exist() {
        // Sort of an integration test - do we want here?
        var fm = new gobotany.filters.FilterManager({pile_slug: 'foo'});
        fm.load_default_filters();
        doh.assertFalse(fm.default_filters.length > 0);
    },
]);
