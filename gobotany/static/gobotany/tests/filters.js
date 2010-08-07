dojo.provide('gobotany.tests.filters');
dojo.require('gobotany.filters');

doh.register('gobotany.tests.core.TestFilterManager',
             [
                 function() {
                     var fm = new gobotany.filters.FilterManager({pile_slug: 'foo'});
                     doh.assertEqual(fm.pile_slug, 'foo');
                 }
             ]);
