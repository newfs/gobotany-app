define([
    'args',
    'jquery',
    'underscore-min',
    'lib/tooltipsy',
    'simplekey/App3',
    'simplekey/Filter',
    'simplekey/FilterController',
    'simplekey/animation',
    'simplekey/cookie',
    'simplekey/glossarize',
    'simplekey/resources',
    'simplekey/ResultsPageState'
], function(args, x, x, x, App3, _Filter, _FilterController,
            animation, cookie, _glossarize, resources, ResultsPageState) {

    var pile_slug = args.pile_slug;
    var helper;  // legacy object; gets set way down at the bottom of this file
    var document_is_ready = $.Deferred();

    $(document).ready(function() {
        document_is_ready.resolve();
    });

    // Dojo code needs globals, so we create some.
    global_speciessectionhelper = null;
    Filter = _Filter;
    FilterController = _FilterController;
    glossarize = _glossarize;

    App3.taxa = Ember.Object.create({
        len: 'Loading',   // placeholder until we have an integer to display
        show_list: false  // whether to show list or grid
    });

    App3.image_types = Ember.ArrayProxy.create({
        content: []
    });

    App3.TaxaView = Ember.View.extend({
        show_listBinding: 'App3.taxa.show_list',
        taxa_countBinding: 'App3.taxa.len',

        switch_photo_list: function(event) {
            // Tell the old Dojo species section helper to switch views.
            if (global_speciessectionhelper)
                global_speciessectionhelper.toggle_view(event);
        }
    });

    /* Async resources and deferreds. */

    var async_key_vector = resources.key_vector('simple');
    var async_pile_taxadata = resources.pile_species(pile_slug);
    var filter_controller_is_built = $.Deferred();

    var pile_taxa_ready = $.Deferred();
    async_pile_taxadata.done(function(taxadata) {
        pile_taxa_ready.resolve(_.pluck(taxadata, 'id'));
    });

    /* Various parts of the page need random access to taxa. */

    App3.taxa_by_sciname = {};
    async_pile_taxadata.done(function(taxadata) {
        _.each(taxadata, function(datum) {
            App3.taxa_by_sciname[datum.scientific_name] = datum;
        });
    });

    /* The FilterController can be activated once we know the full list
       of species that it will be filtering. */

    $.when(async_key_vector, async_pile_taxadata).done(function(kv, taxadata) {
        var simple_key_taxa = kv[0].species;
        var taxadata = _.filter(taxadata, function(taxon) {
            return _.indexOf(simple_key_taxa, taxon.id) != -1;
        });
        App3.set('taxadata', taxadata);  // TODO: put this somewhere else?

        var fc = FilterController.create({
            taxadata: taxadata,
            plain_filters: [],
            add: function(filter) {
                // Keep a separate list of only non-family/genus filters.
                this._super(filter);
                if (filter.slug != 'family' && filter.slug != 'genus')
                    this.plain_filters.addObject(filter);
            }
        });
        App3.set('filter_controller', fc);
        App3.set('family_filter', fc.filtermap.family);
        App3.set('genus_filter', fc.filtermap.genus);
        filter_controller_is_built.resolve();

    });

    $.when(filter_controller_is_built, document_is_ready).done(function() {
        // Hide the "Loading..." spinner.
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

    // Don't bind these new properites until we're sure the filter controller
    // is ready.
    $.when(filter_controller_is_built).done(function() {
        App3.reopen({
            family_choices: function() {
                return choices_that_leave_more_than_zero_taxa(App3.family_filter);
            }.property('filter_controller.@each.value'),

            genus_choices: function() {
                return choices_that_leave_more_than_zero_taxa(App3.genus_filter);
            }.property('filter_controller.@each.value')
        });
    });

    $('#family_clear').live('click', function(event) {
        App3.family_filter.set('value', '');
    });
    $('#genus_clear').live('click', function(event) {
        App3.genus_filter.set('value', '');
    });

    /* Other filters appear along the left sidebar, mediated through
       this convenient FilterView. */

    App3.FilterView = Ember.View.extend({
        templateName: 'filter-view',
        filterBinding: 'content',  // 'this.filter' makes more readable code
        classNameBindings: ['answered'],

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

            if (filter.is_length()) {
                var units = filter.display_units || 'mm';
                return gobotany.utils.pretty_length(units, value);
            }

            return value + '';
        }.property('filter.value'),

        clear: function(event) {
            if (helper.filter_section.working_area)
                helper.filter_section.working_area.dismiss();
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
                helper.filter_section.show_filter_working_onload(filter, y);
            });
        }
    });

    /* The FilterView above is automatically instantiated and managed by
       this CollectionView, which is careful to use the 'plain_filters'
       attribute that omits the family and genus filters. */

    $.when(document_is_ready, filter_controller_is_built).done(function() {
        App3.filters_view = Ember.CollectionView.create({
            tagName: 'ul',
            classNames: ['option-list'],
            contentBinding: 'App3.filter_controller.plain_filters',
            itemViewClass: App3.FilterView
        });
        App3.filters_view.appendTo('#questions-go-here');
    });

    /* Because filters would otherwise constantly change the height of
       the sidebar, we give them their own scrollbar. */

    var scroll_pane = null;
    var user_is_scrolling = true;

    require(['lib/jquery.jscrollpane'], function() {
        $.when(document_is_ready).done(function() {
            scroll_pane = $('.scroll')
                .bind('jsp-scroll-y', function(event) {
                    if (user_is_scrolling)  // because this could be a reinitialise
                        if (helper.filter_section.working_area)
                            helper.filter_section.working_area.dismiss();
                })
                .jScrollPane({
                    maintainPosition: true,
                    stickToBottom: true,
                    verticalGutter: 0,
                    showArrows: true
                });
        });
    });

    /* All filters can be cleared with a single button click. */
    $.when(filter_controller_is_built, document_is_ready).done(function() {
        $('#sidebar a.clear-all-btn').click(function() {
            if (helper.filter_section.working_area !== null)
                helper.filter_section.working_area.dismiss();
            _.each(App3.filter_controller.get('content'), function(filter) {
                filter.set('value', null);
            });
        });
    });

    /* Filters need to be loaded. */

    var use_hash = (window.location.hash !== '') ? true : false;
    if (use_hash) {
        // Restore the state of the page from a URL hash.

        var results_page_state = ResultsPageState.create({
            'hash': window.location.hash
        });
        var filter_slugs = results_page_state.filter_names();
        var filter_values = results_page_state.filter_values();

        $.when(
            filter_controller_is_built,
            resources.pile(pile_slug),
            resources.pile_characters(pile_slug)
        ).done(function(x, pile_info, character_list) {

            var character_map = {};
            var all_filters = character_list.concat(pile_info.default_filters);
            _.each(all_filters, function(info) {
                character_map[info.short_name] = info;
            });

            var default_slugs = _.map(pile_info.default_filters, function(f) {
                return f.short_name;
            });

            var other_slugs = _.difference(filter_slugs, default_slugs);
            var all_slugs = default_slugs.concat(other_slugs);

            _.each(all_slugs, function(slug) {
                if (!_.has(character_map, slug))
                    return;

                // Start an async load in case the user uses the filter.
                resources.character_vector(slug);

                // Create the filter if it does not exist already.
                var info = character_map[slug];
                if (!_.has(App3.filter_controller.filtermap, slug)) {
                    App3.filter_controller.add(Filter.create({
                        slug: info.short_name,
                        value_type: info.value_type,
                        info: info
                    }));
                }

                // Set the filter's value if the hash specified one.
                if (_.has(filter_values, slug)) {
                    var filter = App3.filter_controller.filtermap[slug];
                    var value = filter_values[slug];
                    var async = resources.character_vector(slug);
                    $.when(pile_taxa_ready, async)
                        .done(function(pile_taxa, values) {
                        filter.install_values({
                            pile_taxa: pile_taxa,
                            values: values
                        });
                        filter.set('value', value);
                    });
                }
            });

            // Set any classification filter values specified on the hash.
            if (filter_values['family']) {
                App3.family_filter.set('value', filter_values['family']);
            }
            if (filter_values['genus']) {
                App3.genus_filter.set('value', filter_values['genus']);
            }
            // Set the image type specified on the hash.
            var image_type = results_page_state.image_type();
            if (image_type !== '') {
                console.log('** restore: about to set image type:',
                            image_type);
                App3.set('image_type', image_type);
            }

            // Set the tab view specified on the hash.
            var tab_view = results_page_state.tab_view();
            var is_list_view = (tab_view === 'list') ? true : false;
            console.log('** restore: about to set view: is_list_view:',
                        is_list_view);
            App3.set('taxa.is_list', is_list_view);
        });
    } else {
        // With no hash on the URL, load the default filters for this
        // plant subgroup for a "fresh" load of the page.

        $.when(filter_controller_is_built).done(function() {
            resources.pile(pile_slug).done(function(pile_info) {
                _.each(pile_info.default_filters, function(filter_info) {
                    App3.filter_controller.add(Filter.create({
                        slug: filter_info.short_name,
                        value_type: filter_info.value_type,
                        info: filter_info
                    }));
                    // Go ahead and start an async fetch, to make things
                    // faster in case the user clicks on the filter.
                    resources.character_vector(filter_info.short_name);
                });
            });
        });
    }

    /* When filters change, or other page elements (photo type,
     * tab view) change, update the hash and save it. */

    var save_filter_state = function () {
        var tab_view = App3.taxa.show_list ? 'list' : 'photos';

        var image_type = App3.image_type;
        if (!image_type) {
            // If the image type menu is not ready yet, the page is still
            // loading, so do not save the state yet.
            return;
        }
        var filter_names = Object.keys(App3.filter_controller.filtermap);
        var filter_values = {};
        for (key in App3.filter_controller.filtermap) {
            if (App3.filter_controller.filtermap.hasOwnProperty(key)) {
                if (App3.filter_controller.filtermap[key].value &&
                    App3.filter_controller.filtermap[key].value.length > 0) {

                    filter_values[key] =
                        App3.filter_controller.filtermap[key].value;
                }
            }
        }

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

        cookie('last_plant_id_url', window.location.href, {path: '/'});
    };

    App3.addObserver('filter_controller.@each.value', function() {
        save_filter_state();
    });
    App3.addObserver('image_type', function() {
        save_filter_state();
    });
    App3.addObserver('taxa.show_list', function() {
        save_filter_state();
    });

    /* More filters can be fetched with the "Get More Questions" button. */

    var checked_groups = [];  // remembers choices from last time

    $.when(document_is_ready).done(function() {
        $('#sidebar .get-choices').click(function() {
            if (helper.filter_section.working_area !== null)
                helper.filter_section.working_area.dismiss();

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

        simplekey_resources.pile_best_characters({
            pile_slug: pile_slug,
            species_ids: App3.filter_controller.taxa,
            character_group_ids: checked_groups,
            exclude_characters: existing
        }).done(receive_new_filters);

        Shadowbox.close();
    });

    var receive_new_filters = function(items) {
        if (items.length === 0) {
            gobotany.utils.notify(
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
        gobotany.utils.notify('More questions added');
    };

    // On modern browsers that support the hashchange event, allow the
    // user to "undo" actions via the Back button.
    $(window).bind('hashchange', function() {
        var current_url = window.location.href;

        var last_plant_id_url = cookie('last_plant_id_url');
        if (last_plant_id_url === undefined) {
            last_plant_id_url = '';
        }

        // When going forward and applying values, etc., the current URL and
        // last plant ID URL are always the same. After pressing Back, they
        // are different.
        if (current_url !== last_plant_id_url) {
            // Now reload the current URL, which reloads everything on the
            // page and sets it up all again. This means a little more going
            // on that usually seen with an Undo command, but is pretty
            // quick and allows for robust yet uncomplicated Undo support.
            window.location.reload();
        }
    });

    //

    require([
        'simplekey/results_overlay',
        'simplekey/results_photo_menu'
    ]);

    if (true) {
        /* Glue: tell Dojo when the set of selected species
           changes. */

        App3.reopen({
            tell_dojo: function() {
                var taxa = App3.filter_controller.taxa;
                var t = _.filter(App3.taxadata, function(item) {
                    return _.indexOf(taxa, item.id) != -1;
                });
                t.sort(function(a, b) {
                    return a.scientific_name < b.scientific_name ? -1 : 1;
                });
                dojo.publish('/filters/query-result', [{species_list: t}]);
            }.observes('filter_controller.taxa')
        });

        require([
            'order!/static/gobotany/utils.js',
            'order!/static/gobotany/sk/photo.js',
            'order!/static/gobotany/sk/results.js',
            'order!/static/gobotany/sk/SpeciesSectionHelper.js',
            'order!/static/gobotany/sk/working_area.js',
            'order!/static/gobotany/sk/SearchSuggest.js'
        ], function() {
            require([
                'order!activate_search_suggest',
                'order!activate_image_gallery',
                'sidebar',
                'shadowbox',
                'shadowbox_init'
            ], function() {
                dojo.require('gobotany.sk.results');
                dojo.addOnLoad(function() {
                    helper = gobotany.sk.results.ResultsHelper(args.pile_slug);
                });
            });
        });
    }
});
