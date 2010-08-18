dojo.provide('gobotany.sk.tests.run');
dojo.require('gobotany.sk.results');
var data;
dojo.addOnLoad(
    function () {
        // Add a customized filter_manager with canned json data
        filter_manager = new gobotany.filters.FilterManager(
            {pile_slug: 'lycophytes',
             pile_url: './lycophytes.json',
             taxon_url: './lycophytes_taxon.json'});
        
        // Load images the into the page
        gobotany.sk.results.run_filtered_query();
        
        doh.register('gobotany.tests.results.TestImageSelect', 
[
    function test_populate_image_types() {
        var select = dojo.byId('image-type-selector');
        doh.assertEqual(0, select.options.length);
        gobotany.sk.results.populate_image_types(data);
        doh.assertEqual(5, select.options.length);
        doh.assertEqual('habit', select.value);
        doh.assertEqual('branches', select.options[0].value);
    },
    function test_select_image_type() {
        var first_image = dojo.query('#plant-dendrolycopodium-dendroideum img')[0];
        var next_image = dojo.query('#plant-huperzia-lucidula img')[0];
        var later_image = dojo.query('#plant-spinulum-annotinum img')[0];
        // Test the current values, the first has an image with a src attribute
        doh.assertEqual('/media/content-thumbs/species/dendrolycopodium-dendroideum-ha-dkausen-1_jpg_110x110_q85.jpg',
                        dojo.attr(first_image, 'src'));
        
        // The next one is similar
        doh.assertEqual('/media/content-thumbs/species/huperzia-lucidula-ha-gmittelhauser-1_jpg_110x110_q85.jpg',
                        dojo.attr(next_image, 'src'));
        
        // The final image has no src attribute, but has the url in a
        // special attribute to retrieve later
        doh.assertEqual(undefined,
                        dojo.attr(later_image, 'src'));
        doh.assertEqual('/media/content-thumbs/species/spinulum-annotinum-ha-mlovit-1_jpg_110x110_q85.jpg',
                        dojo.attr(later_image, 'x-tmp-src'));
        var select = dojo.byId('image-type-selector');
        // Switch to branches
        select.value = 'branches';
        gobotany.sk.results.load_selected_image_type();
        // There is no matching branch image for the first item, so it is hidden
        doh.assertEqual('none', dojo.style(first_image, 'display'));
        // A placeholder has been added wher the image was
        doh.assertEqual(1, dojo.query('+ .MissingImage', first_image).length);
        // The next image has had it's src updated
        doh.assertEqual('/media/content-thumbs/species/huperzia-lucidula-br-mlovit-1_jpg_110x110_q85.jpg',
                        dojo.attr(next_image, 'src'));
        // The latter image has an updated x-tmp-src
        doh.assertEqual(undefined,
                        dojo.attr(later_image, 'src'));
        doh.assertEqual('/media/content-thumbs/species/spinulum-annotinum-br-dkausen-1_jpg_110x110_q85.jpg',
                        dojo.attr(later_image, 'x-tmp-src'));                             
        select.value = 'habit';
        gobotany.sk.results.load_selected_image_type();
    },
    function test_select_image_type_multiple() {
        var first_image = dojo.query('#plant-dendrolycopodium-dendroideum img')[0];
        var select = dojo.byId('image-type-selector');
        // Switch to branches
        select.value = 'branches';
        gobotany.sk.results.load_selected_image_type();
        // Switch back
        select.value = 'habit';
        gobotany.sk.results.load_selected_image_type();
        // Note that the image is visible, the url is correct, and the
        // missing image placeholder is gone
        doh.assertEqual('inline', dojo.style(first_image, 'display'));
        doh.assertEqual('/media/content-thumbs/species/dendrolycopodium-dendroideum-ha-dkausen-1_jpg_110x110_q85.jpg',
                        dojo.attr(first_image, 'src'));
        doh.assertEqual(0, dojo.query('+ .MissingImage', first_image).length);
    }
]);

        doh.register('gobotany.tests.results.TestLazyImageLoad', 
[
    function test_load_unloaded_page() {
        var next_page = dojo.byId('plant-page-2');
        var unloaded_image = dojo.query('#plant-spinulum-annotinum img')[0];
        // The page has not yet been loaded
        doh.assertEqual('false', dojo.attr(next_page, 'x-loaded'));
        // The image has no src attribute, but has the url in a
        // special attribute to retrieve later
        doh.assertEqual(undefined,
                        dojo.attr(unloaded_image, 'src'));
        doh.assertEqual('/media/content-thumbs/species/spinulum-annotinum-ha-mlovit-1_jpg_110x110_q85.jpg',
                        dojo.attr(unloaded_image, 'x-tmp-src'));
        // All of the images on the page have no src attribute
        doh.assertEqual(4, dojo.query('img[src=]', next_page).length);
        
        // Load the page
        gobotany.sk.results.load_page(next_page);
        // The page is marked as loaded
        doh.assertEqual('true', dojo.attr(next_page, 'x-loaded'));
        // The image has a src attribute now.
        doh.assertEqual('/media/content-thumbs/species/spinulum-annotinum-ha-mlovit-1_jpg_110x110_q85.jpg',
                        dojo.attr(unloaded_image, 'src'));
        // All of the images on the page now have a src attribute
        doh.assertEqual(0, dojo.query('img[src=]', next_page).length);
    }
]);
    });
// Once the results are loaded run the tests
dojo.subscribe('results_loaded', function (message) { data = message; doh.run()});