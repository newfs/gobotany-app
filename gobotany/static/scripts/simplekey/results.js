define([
    'util/document_is_ready',
    'bridge/jquery',
    'bridge/jquery.cookie',
    'bridge/jquery.jscrollpane',
    'bridge/ember',
    'bridge/shadowbox',
    'util/shadowbox_init',
    'bridge/underscore',
    'simplekey/App3',
    'simplekey/Filter',
    'simplekey/FilterController',
    'simplekey/animation',
    'simplekey/glossarize',
    'simplekey/resources',
    'simplekey/ResultsPageState',
    'simplekey/results_overlay',
    'simplekey/SpeciesSection',
    'simplekey/working_area',
    'simplekey/utils',
    'util/activate_image_gallery',
    'util/lazy_images',
    'util/sidebar'
], function(
    document_is_ready, $, x, x, Ember, Shadowbox, shadowbox_init, _,
    App3, Filter, FilterController, animation, glossarize, resources,
    ResultsPageState, results_overlay_init, SpeciesSection,
    working_area_module, utils, image_gallery, lazy_images, sidebar
) {return {

results_page_init: function(args) {
    var pile_slug = args.pile_slug;

    sidebar.setup();

    var species_section = new SpeciesSection();
    var species_section_ready = $.Deferred();

    $.when(
        document_is_ready,
        filtered_sorted_taxadata_ready,
        taxa_by_sciname_ready
    ).done(function() {
        species_section.init(pile_slug, plant_divs_ready);
        species_section_ready.resolve();
    });

    App3.set('show_grid', true);
    App3.set('show_list', false);
    App3.set('matching_species_count', 'Loading');

    App3.image_types = Ember.ArrayProxy.create({
        content: []
    });

    /* Async resources and deferreds. */

    var all_filters_ready = $.Deferred();
    var filter_controller_is_built = $.Deferred();
    var filtered_sorted_taxadata_ready = $.Deferred();
    var image_type_ready = $.Deferred();
    var pile_taxa_ready = $.Deferred();
    var pile_taxadata_ready = resources.pile_species(pile_slug);
    var plant_divs_ready = $.Deferred();
    var taxa_by_sciname_ready = $.Deferred();

    if (args.key == 'simple') {
        var key_vector_ready = resources.key_vector('simple');
    } else {
        // The "full" key includes every species in the entire pile
        var key_vector_ready = $.Deferred();
        pile_taxa_ready.done(function(species_ids) {
            key_vector_ready.resolve([{species: species_ids}]);
        });
    }
    pile_taxadata_ready.done(function(taxadata) {
        pile_taxa_ready.resolve(_.pluck(taxadata, 'id'));
    });

    App3.addObserver('image_type', function() {
        image_type_ready.resolve();
    });

    /* Get the overlay started. */

    results_overlay_init(pile_slug, key_vector_ready, pile_taxa_ready);

    /* Various parts of the page need random access to taxa. */

    App3.taxa_by_sciname = {};
    pile_taxadata_ready.done(function(taxadata) {
        _.each(taxadata, function(datum) {
            App3.taxa_by_sciname[datum.scientific_name] = datum;
            taxa_by_sciname_ready.resolve();
        });
    });

    /* Create a list of character groups from the pile's filters. */

    resources.pile(pile_slug).done(function(pile_info) {
        var $ul = $('ul.char-groups').empty();
        _.each(pile_info.character_groups, function(character_group) {
            $ul.append(
                $('<li>').append(
                    $('<label>').append(
                        $('<input>', {type: 'checkbox',
                                      value: character_group.id}),
                        ' ' + character_group.name
                    )
                )
            );
        });
    });

    /* The FilterController can be created once we know the full list of
       species that it will be filtering and once we have all of the
       filters that it should include initially. */

    $.when(
        all_filters_ready,
        key_vector_ready,
        pile_taxadata_ready
    ).done(function(filters_config, key_vector, taxadata) {
        var simple_key_taxa = key_vector[0].species;
        var taxadata = _.filter(taxadata, function(taxon) {
            return _.indexOf(simple_key_taxa, taxon.id) != -1;
        });
        App3.set('taxadata', taxadata);  // TODO: put this somewhere else?

        var fc = FilterController.create({
            taxadata: taxadata,

            // Keep a separate list of only non-family/genus filters, to
            // be displayed as a list in the sidebar.
            plain_filters: [],
            add: function(filter) {
                this._super(filter);
                if (filter.slug != 'family' && filter.slug != 'genus')
                    this.plain_filters.addObject(filter);
            }
        });

        // FIRST we install the family and genus filters on App3, THEN
        // set their values, because doing it the other way introduces a
        // race condition where their initial hash-set values do not
        // appear in their select boxes.

        App3.set('family_filter', fc.filtermap.family);
        App3.set('genus_filter', fc.filtermap.genus);

        fc.filtermap.family.set('value', filters_config.family_name);
        fc.filtermap.genus.set('value', filters_config.genus_name);

        _.each(filters_config.other_filters, $.proxy(fc.add, fc));

        App3.set('filter_controller', fc);

        filter_controller_is_built.resolve();
    });

    $.when(filter_controller_is_built, document_is_ready).done(function() {
        // Hide the "Loading..." spinner in the sidebar.
        $('.loading').hide();
    });

    /* The Family and Genus filters are Ember-powered <select> elements
       that the following logic keeps updated at all times with the set
       of legal family and genus values. */

    var choices_that_leave_more_than_zero_taxa = function(filter) {
        var other_taxa = App3.filter_controller.compute(filter);
        var keepers = _.filter(filter.values, function(value) {
            return _.intersect(value.taxa, other_taxa).length;
        });
        var choices = _.pluck(keepers, 'choice');
        choices.sort();
        choices.splice(0, 0, '');  // to "not select" a family or genus
        return choices;
    };

    App3.reopen({
        family_choices: function() {
            var choices = [];
            if (App3.family_filter) {
                choices = choices_that_leave_more_than_zero_taxa(
                    App3.family_filter);
            }
            return choices;
        }.property('filter_controller.taxa'),

        genus_choices: function() {
            var choices = [];
            if (App3.genus_filter) {
                choices = choices_that_leave_more_than_zero_taxa(
                    App3.genus_filter);
            }
            return choices;
        }.property('filter_controller.taxa'),

        /* These two properties translate between our internal filter
           value of "null" and the empty string that the <select> needs
           when nothing is selected, and also prevent */

        family_value: function(key, new_value) {
            if (! App3.family_filter)
                return '';
            if (arguments.length === 1)  // getter
                return App3.family_filter.get('value') || '';
            else
                App3.family_filter.set('value', new_value || null);
        }.property('family_filter.value'),

        genus_value: function(key, new_value) {
            if (! App3.genus_filter)
                return '';
            if (arguments.length === 1)  // getter
                return App3.genus_filter.get('value') || '';
            else
                App3.genus_filter.set('value', new_value || null);
        }.property('genus_filter.value')
    });

    $('#family_clear').live('click', function(event) {
        App3.set('family_value', '');
    });
    $('#genus_clear').live('click', function(event) {
        App3.set('genus_value', '');
    });

    /* Other filters appear along the left sidebar, with each filter's
       div being supplied with information through an instance of this
       convenient FilterView. */

    var working_area = null;

    var show_working_area = function(filter, y) {
        // Dismiss old working area, to avoid having an Apply button
        // that is wired up to two different filters!
        dismiss_any_working_area();

        var C = working_area_module.select_working_area(filter);

        working_area = new C();
        working_area.init({
            div: $('div.working-area')[0],
            filter: filter,
            y: y
        });

        sidebar.set_height();
    };

    var dismiss_any_working_area = function() {
        if (working_area !== null) {
            working_area.dismiss();
            working_area = null;
        }
    }

    $(document).keydown(function(e) {
        if (event.which === 27) {       // "Esc"
            event.preventDefault();
            dismiss_any_working_area();
        }
    });

    App3.FilterView = Ember.View.extend({
        templateName: 'filter-view',
        filterBinding: 'content',  // 'this.filter' makes more readable code
        classNameBindings: ['answered'],

        elementId: function() {
            return this.content.slug;
        }.property('content'),

        didInsertElement: function() {
            var id = this.get('elementId');
            glossarize($('#' + id + ' span.name'));
        },

        answered: function() {
            // Return whether to assign the "answered" CSS class.
            return !! this.filter.value;
        }.property('filter.value'),

        display_value: function() {
            var filter = this.get('filter');
            var value = filter.get('value');

            if (value === null)
                return '';   // Do not display a "don't know" value

            if (value === 'NA')
                return 'does not apply';

            if (filter.value_type === 'TEXT')
                return filter.choicemap[value].friendly_text || value;

            if (filter.is_length) {
                var units = filter.display_units || 'mm';
                return utils.pretty_length(units, value);
            }

            return value + '';
        }.property('filter.value'),

        clear: function(event) {
            dismiss_any_working_area();
            this.filter.set('value', null);
        },

        click: function(event) {
            if ($(event.target).hasClass('clear-filter'))
                return;

            var filter = this.get('filter');
            var $target = $(event.target).closest('li');

            $('.option-list li .active').removeClass('active');
            $target.addClass('active');

            var y = $target.offset().top - 15;
            var async = resources.character_vector(this.filter.slug);
            $.when(pile_taxa_ready, async).done(function(pile_taxa, values) {
                filter.install_values({pile_taxa: pile_taxa, values: values});
                show_working_area(filter, y);
            });
        }
    });

    /* The FilterView above is automatically instantiated and managed by
       this CollectionView, which is careful to use the 'plain_filters'
       attribute that omits the family and genus filters. */

    $.when(
        document_is_ready,
        filter_controller_is_built,
        species_section_ready
    ).done(function() {
        App3.filters_view = Ember.CollectionView.create({
            tagName: 'ul',
            classNames: ['option-list'],
            contentBinding: 'App3.filter_controller.plain_filters',
            itemViewClass: App3.FilterView
        });
        App3.filters_view.appendTo('#questions-go-here');

        App3.species_view_tabs = Ember.View.create({
            templateName: 'species-view-tabs',
            tagName: 'ul',

            choose_grid_view: function() {
                if (App3.show_grid) return;
                App3.set('show_grid', true);
                App3.set('show_list', false);
                species_section.display_results();
            },
            choose_list_view: function() {
                if (App3.show_list) return;
                App3.set('show_list', true);
                App3.set('show_grid', false);
                species_section.display_results();
            }
        });
        App3.species_view_tabs.appendTo('#results-tabs');

        App3.species_view_toggle = Ember.View.create({
            templateName: 'species-view-toggle',
            tagName: 'p',
            classNames: ['list-all'],

            switch_species_view: function() {
                if (App3.show_grid)
                    App3.species_view_tabs.choose_list_view();
                else
                    App3.species_view_tabs.choose_grid_view();
            }
        });
        App3.species_view_toggle.appendTo('#main');
    });

    /* Because filters would otherwise constantly change the height of
       the sidebar, we give them their own scrollbar. */

    var scroll_pane = null;
    var user_is_scrolling = true;

    $.when(document_is_ready).done(function() {
        scroll_pane = $('.scroll')
            .bind('jsp-scroll-y', function(event) {
                // Make sure this is not a reinitialise
                if (user_is_scrolling)
                    dismiss_any_working_area();
            })
            .jScrollPane({
                maintainPosition: true,
                stickToBottom: true,
                verticalGutter: 0,
                showArrows: true
            });

        // Re-initialise the scroll pain regularly because new
        // filters will get drawn and because existing filters will
        // change their height as values get set and cleared.  It
        // can only resize when the working area is gone, however;
        // adjusting the scroll pane closes the working area!

        setInterval(function() {
            if (working_area === null)
                scroll_pane.data('jsp').reinitialise();
        }, 500);
    });

    /* All filters can be cleared with a single button click. */
    $.when(filter_controller_is_built, document_is_ready).done(function() {
        $('#sidebar a.clear-all-btn').click(function() {
            dismiss_any_working_area();
            var plains = App3.filter_controller.get('plain_filters');
            _.each(plains, function(filter) {
                filter.set('value', null);
            });
            App3.set('family_value', '');
            App3.set('genus_value', '');
        });
    });

    /* Update the hash to reflect the page state and save the entire
     * URL to a cookie. This is to be called when filters or other
     * page elements (image type, tab view) change.
     */
    var save_page_state = function() {
        var tab_view = App3.show_list ? 'list' : 'photos';

        var image_type = App3.get('image_type');
        if (!image_type) {
            // If the image type menu is not ready yet, the page is still
            // loading, so do not save the state yet.
            return;
        }

        // Get all the current filter names and values.
        var filter_names = Object.keys(App3.filter_controller.filtermap);
        var filter_values = {};
        var filter;
        for (key in App3.filter_controller.filtermap) {
            if (App3.filter_controller.filtermap.hasOwnProperty(key)) {
                filter = App3.filter_controller.filtermap[key];
                if (filter.value && filter.value.toString().length > 0) {
                    filter_values[key] = filter.value;
                }
            }
        }

        // Create a hash for this page state.
        var results_page_state = ResultsPageState.create({
            'filter_names': filter_names,
            'filter_values': filter_values,
            'image_type': image_type,
            'tab_view': tab_view
        });
        var hash = results_page_state.hash();

        // Usually, do not replace the current Back history entry; rather,
        // create a new one, to enable the user to move back and forward
        // through their keying choices.
        var create_new_history_entry = true;

        // However, upon the initial entry to plant ID keying (where there's
        // no hash yet), do not create a new Back history entry when replacing
        // the hash. This is to help avoid creating a "barrier" when the user
        // tries to navigate back to the pile ID pages using the Back button.
        if (window.location.hash === '') {   // empty hash: initial page load
            create_new_history_entry = false;
        }

        var url = window.location.href.split('#')[0] + hash;
        if (create_new_history_entry) {
            window.location.assign(url);
        }
        else {
            window.location.replace(url);
        }

        $.cookie('last_plant_id_url', window.location.href, {path: '/'});
    };

    /* Set up observers so that when page elements change, the URL hash
     * will be updated and the URL will be saved.
     */
    filter_controller_is_built.done(function() {
        save_page_state();

        App3.addObserver('filter_controller.@each.value', function() {
            save_page_state();
        });
        App3.addObserver('image_type', function() {
            save_page_state();
        });
        App3.addObserver('show_list', function() {
            save_page_state();
        });
    });

    /* Filters need to be loaded. */

    var use_hash = (window.location.hash !== '') ? true : false;
    if (use_hash) {
        /* Restore the state of the page from a URL hash.  This leads to
           a bit of complexity, since, for example, we will have to do a
           separate async fetch of every filter that the user was busy
           using when the hash that we are restoring got saved. */

        var results_page_state = ResultsPageState.create({
            'hash': window.location.hash
        });
        var filter_slugs = results_page_state.filter_names();
        var filter_values = results_page_state.filter_values();

        /* Immediately set the image type specified on the hash, so that
           the page does not first fall back on the default image type
           for this pile and thus have to load all images twice. */

        var image_type = results_page_state.image_type();
        if (image_type !== '') {
            // Simply setting the image_type, without also making
            // sure that it is listed as a valid value in the
            // image_types array, will cause the Ember.Select view
            // to treat the value as illegal and reset the value
            // back to "undefined", which kicks off several
            // expensive rounds of repopulating the species area.
            if (App3.image_types.get('content').length === 0) {
                App3.image_types.set('content', [image_type]);
            }
            App3.set('image_type', image_type);

        }

        /* Also immediately set the tab view specified on the hash. */

        var tab_view = results_page_state.tab_view();
        var is_list_view = (tab_view === 'list') ? true : false;
        App3.set('show_grid', ! is_list_view);
        App3.set('show_list', is_list_view);

        /* But our remaining actions will take time, and have to wait
           until we have retrieved some information about this pile. */

        $.when(
            resources.pile(pile_slug),
            resources.pile_characters(pile_slug)
        ).done(function(pile_info, character_list) {

            var character_map = {};
            var all_filters = character_list.concat(pile_info.default_filters);
            _.each(all_filters, function(info) {
                character_map[info.short_name] = info;
            });

            // The default filters are always listed first.

            var default_slugs = _.pluck(pile_info.default_filters,
                                        'short_name');
            var other_slugs = _.difference(filter_slugs, default_slugs);
            var all_slugs = default_slugs.concat(other_slugs);

            // Create filters; set values; give them to the controller.

            var filter_readys = [];
            var filters_config = {
                family_name: filter_values['family'] || null,
                genus_name: filter_values['genus'] || null,
                other_filters: []
            };

            _.each(all_slugs, function(slug) {
                var info = character_map[slug];
                if (typeof info === 'undefined')
                    return;

                var filter = Filter.create({
                    slug: info.short_name,
                    value_type: info.value_type,
                    info: info
                });
                filters_config.other_filters.push(filter);

                if (_.has(filter_values, slug)) {
                    filter.set('value', filter_values[slug]);

                    var deferred = $.Deferred();
                    filter_readys.push(deferred);
                    $.when(
                        pile_taxa_ready,
                        resources.character_vector(slug)
                    ).done(function(pile_taxa, values) {
                        filter.install_values({
                            pile_taxa: pile_taxa,
                            values: values
                        });
                        deferred.resolve();
                    });
                }
            });

            $.when.apply(this, filter_readys).done(function() {
                all_filters_ready.resolve(filters_config);
            });

        });
    } else {
        /* When the URL contains no hash, we get to load the default
           filters in a single fetch by grabbing the pile resources, so
           all_filters_ready depends upon only a single async request. */

        resources.pile(pile_slug).done(function(pile_info) {
            var filters_config = {
                family_name: null,
                genus_name: null,
                other_filters: []
            };
            _.each(pile_info.default_filters, function(filter_info) {
                var filter = Filter.create({
                    slug: filter_info.short_name,
                    value_type: filter_info.value_type,
                    info: filter_info
                });
                filters_config.other_filters.push(filter);
            });
            all_filters_ready.resolve(filters_config);
        });
    }

    /* More filters can be fetched with the "Get More Questions" button. */

    var checked_groups = [];  // remembers choices from last time

    $.when(document_is_ready).done(function() {
        $('#sidebar .get-choices').click(function() {
            dismiss_any_working_area();

            Shadowbox.open({
                content: $('#modal').html(),
                player: 'html',
                height: 450,
                options: {
                    fadeDuration: 0.1,
                    onFinish: function() {
                        // Re-check any check boxes that were set last time.
                        $('#sb-container input').each(function(i, input) {
                            var value = $(input).val();
                            var check = (_.indexOf(checked_groups, value) != -1);
                            $(input).prop('checked', check);
                        });
                        $('#sb-container a.get-choices')
                            .addClass('get-choices-ready');  // for tests
                    }
                }
            });
        });
    });

    $('#sb-container a.get-choices').live('click', function() {
        checked_groups = [];  // reset array in enclosing scope
        $('#sb-container input').each(function(i, input) {
            if ($(input).prop('checked'))
                checked_groups.push($(input).val());
        });

        var existing = [];
        _.each(App3.filter_controller.content, function(filter) {
            existing.push(filter.slug);
        });
        simplekey_resources.more_questions({
            pile_slug: pile_slug,
            species_ids: App3.filter_controller.taxa,
            character_group_ids: checked_groups,
            exclude_characters: existing
        }).done(receive_new_filters);

        Shadowbox.close();
    });

    var receive_new_filters = function(items) {
        if (items.length === 0) {
            utils.notify(
                'No more questions left for the boxes checked');
            return;
        }
        _.each(items, function(filter_info) {
            App3.filter_controller.add(Filter.create({
                slug: filter_info.short_name,
                value_type: filter_info.value_type,
                info: filter_info
            }));
        });
        Ember.run.next(function() {
            var $filters = $('#sidebar ul li');
            var $new = $filters.slice($filters.length - items.length);
            animation.bright_change($new);
            scroll_pane.data('jsp').reinitialise();
            scroll_pane.data('jsp').scrollToPercentY(100, true);
        });
        utils.notify('More questions added');
    };

    // On modern browsers that support the hashchange event, allow the
    // user to "undo" actions via the Back button.
    $(window).bind('hashchange', function() {
        var current_url = window.location.href;

        var last_plant_id_url = $.cookie('last_plant_id_url');
        if (last_plant_id_url === null) {
            // The cookie request returned null, so cookie support must
            // be unavailable. Consequently, cannot support the Back button.
            return;
        }
        else {
            if (last_plant_id_url === undefined) {
                last_plant_id_url = '';
            }

            // When going forward and applying values, etc., the current URL
            // and last plant ID URL are always the same. After pressing
            // Back, they are different.
            if (current_url !== last_plant_id_url) {
                // Now reload the current URL, which reloads the page
                // and sets everything up again. Although it arguably
                // would be slicker to restore withou a page reload,
                // reloading is still fairly quick and avoids the code
                // having to manange history lists. It also makes it
                // easy to support coming back to a Level 3 page from
                // a species page and not losing the history stack.
                window.location.reload();
            }
        }
    });

    // Several places on the page display how many species there are.

    var update_count_animation = null;
    var update_counts = function(species_list) {
        App3.set('matching_species_count', species_list.length);

        var $spans = $('.species-count-heading > span');
        $spans.stop();
        animation.bright_change($spans, {end_color: '#F0F0C0',
                                         duration: 2000});
    };

    /* How we load images into the species area. */

    var load_selected_image_type = function() {
        var image_type = App3.get('image_type');
        if (!image_type)
            // No image types available yet, so skip for now
            return;

        /* Replace the image for each plant on the page */

        $('div.plant img').each(function(i, img) {

            // See if the taxon has an image for the new image type.
            var $img = $(img);
            var scientific_name = $img.attr('x-plant-id');
            var taxon = App3.taxa_by_sciname[scientific_name];
            var new_image = _.find(taxon.images, function(image) {
                return image.type === image_type});

            if (new_image) {
                $img.attr('data-lazy-img-src', new_image.thumb_url);
                $img.attr('alt', new_image.title);
                // Hide the empty box if it exists and make
                // sure the image is visible.
                $img.find('+ div.missing-image').remove();
                $img.css('display', 'inline');

            } else if ($img.css('display') !== 'none') {
                // If there's no matching image display the
                // empty box and hide the image
                $img.css('display', 'none');
                $img.parent().append($('<div>', {
                    'class': 'missing-image',
                    'html': '<p>Image not available yet</p>'
                }));
            }
        });
    }

    // Final pieces of page load cascade.

    lazy_images.start();

    var compute_filtered_sorted_taxadata = function() {
        var taxa = App3.filter_controller.taxa;
        var t = _.filter(App3.taxadata, function(item) {
            return _.indexOf(taxa, item.id) != -1;
        });
        t.sort(function(a, b) {
            return a.scientific_name < b.scientific_name ? -1 : 1;
        });
        App3.set('filtered_sorted_taxadata', t);
        filtered_sorted_taxadata_ready.resolve();
    }

    App3.reopen({
        run_filtered_sorted_taxadata: function() {
            compute_filtered_sorted_taxadata();
            filtered_sorted_taxadata_ready.resolve();
        }.observes('filter_controller.taxa')
    });

    $.when(
        species_section_ready,
        filtered_sorted_taxadata_ready,
        plant_divs_ready
    ).done(function(rh) {
        update_counts(App3.filtered_sorted_taxadata);
        species_section.display_results(App3.filtered_sorted_taxadata);
        load_selected_image_type();
        lazy_images.load();

        App3.addObserver('filtered_sorted_taxadata', function() {
            update_counts(App3.filtered_sorted_taxadata);
            species_section.display_results(App3.filtered_sorted_taxadata);
        });

        App3.addObserver('image_type', function() {
            load_selected_image_type();
            lazy_images.load();
        });
    });
}}});
