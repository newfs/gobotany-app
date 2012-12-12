define([
    'bridge/jquery',
    'bridge/jquery.mousewheel',
    'bridge/underscore',
    'lib/Hash',
    'plantpreview/popup',
    'util/glossarizer',
    'util/lazy_images',
    'util/tooltip'
], function(
    $, ignore, _, Hash, plantpreview_popup,
    glossarizer, lazy_images, tooltip_js
) {$(document).ready(function() {

    /* Remove spinner that is hiding couplets until we can arrange them. */

    $('.wait-spinner').removeClass('wait-spinner');

    /* Enable lazy image loading. */

    lazy_images.start();

    /* Glossarize lead texts. */

    glossarizer.glossarize($('.flora-nova-angliae-text p, .couplets .lead'));

    /* Rewrite couplet IDs so that #-links will no longer match; this
       prevents a change to the URL hash from making the browser think
       that it should visit a different part of the page without letting
       us animate the transition. */

    $('.couplet').each(function(i, ul) {
        var id = $(ul).attr('id');
        if (id)
            $(ul).attr('id', 'c' + id);  // make 'c2' into 'cc2'
    });

    /* Canonical way of forming a URL to a taxon. */

    var is_group = function(name) {
        return name.toLowerCase().indexOf('group') === 0;
    };

    var is_species = function(name) {
        return (!is_group(name)) && (name.indexOf(' ') !== -1);
    };

    var taxon_url = function(name) {
        var name = name.toLowerCase();
        if (is_group(name))
            return '/dkey/' + name.replace(' ', '-') + '/';
        else if (is_species(name))
            return '/species/' + name.replace(' ', '/') +
                '/?key=dichotomous#dkey';
        else
            return '/dkey/' + name + '/';
    };

    var $taxon_anchor = function(name) {
        var url = taxon_url(name);
        if (is_species(name))
            return $('<a/>', {'href': url}).append($('<i/>', {'text': name}));
        else
            return $('<a/>', {'href': url, 'text': name});
    };

    /* Visiting particular couplets. */

    var go_back_text = 'GO BACK';
    var active_id = 'c1';
    var bottom_id = 'c1';

    /* Save the original text of each orange button, since we will have
       to rewrite some of them to say "Go back" as the user descends
       down the hierarchy. */

    $('.lead .button').each(function() {
        $(this).attr('original-text', $(this).text());
    });

    /* The Big Function that gets run when our URL hash changes. */

    var transition_to_hash = function(new_hash, is_initial) {

        var duration = is_initial ? 0 : 200;
        if (!is_initial)
            $('.couplet:animated').stop();

        /* Parse the hash: "c2,c3" means that we are focused on
           answering Couplet 2 but that we got there by clicking "GO
           BACK" when Couplet 3 was highlighted, so Couplet 3 should
           also be expanded and visible but without being highlighted in
           green. If the hash is simply a single couplet ID, like "c3",
           then that single couplet is both the "bottom" of the
           currently-visible hierarchy, and is also the current couplet
           highlighted for choosing. */

        if (!new_hash)
            new_hash = 'c1';

        var comma_at = new_hash.indexOf(',');
        if (comma_at === -1) {
            active_id = new_hash;
            bottom_id = new_hash;
        } else {
            active_id = new_hash.substring(0, comma_at);
            bottom_id = new_hash.substring(comma_at + 1);
        }

        /* First, reset all state. */

        $all_couplets = $('.couplet');
        $all_leads = $('.lead');
        $all_buttons = $all_leads.find('.button');

        $all_couplets.removeClass('active');
        $all_leads.removeClass('chosen go-back original-choice alt-choice');
        $all_buttons.each(function() {
            $(this).text($(this).attr('original-text'));
        });

        /* The hash determines what we display. */

        if (active_id === 'all') {
            var leads_to_show = $all_leads.toArray();
        } else {
            var $active = $('#c' + active_id);
            var $bottom = $('#c' + bottom_id);
            var $active_leads = $active.children('li').children('.lead');
            var $bottom_leads = $bottom.children('li').children('.lead');
            var $parent_leads = $active.parents('li').children('.lead');
            var $ancestor_leads = $bottom.parents('li').children('.lead');
            var leads_to_show = $active_leads.toArray().concat(
                $bottom_leads.toArray(), $ancestor_leads.toArray());

            $active.addClass('active');
            $parent_leads.addClass('chosen');
            $parent_leads.find('.button').text(go_back_text);
        }

        /* Apply special classes to the leads of a couplet to which the
           user has returned through a "Go back" button. */

        if (active_id !== bottom_id) {
            var $lead_a = $active_leads.eq(0);
            var $lead_b = $active_leads.eq(1);
            var $li_a = $lead_a.closest('li');
            if ($.contains($li_a[0], $bottom[0])) {
                $lead_a.addClass('original-choice');
                $lead_b.addClass('alt-choice');
            } else {
                $lead_a.addClass('alt-choice');
                $lead_b.addClass('original-choice');
            }
        }

        /* Visit every lead and make it appear or disappear. */

        $all_leads.each(function(i, div) {
            var show_this_one = (leads_to_show.indexOf(div) !== -1);
            if (show_this_one) {
                $(div).slideDown(duration);
            } else {
                $(div).slideUp(duration);
            }
        });

        /* Enable or disable the "show all" button. */

        var button = $('.show-all-button');
        if (active_id === 'all') {
            button.html('Show First Couplet').attr('href', '#');
        } else {
            button.html('Show All Couplets').attr('href', '#all');
        }

        /* Restrict the set of images to taxa beneath this couplet. */

        show_appropriate_images();
    }

    $('.lead .button').on('click', function() {
        if ($(this).text() === go_back_text) {
            var raw_active_id = $(this).closest('.couplet').attr('id');
            var new_active_id = raw_active_id.replace('cc', 'c');
            Hash.go(new_active_id + ',' + bottom_id);
            return false;
        }
    });

    /* Clicking on "See list of 7 genera in 1b" should display them. */

    var $shadow = $('<div>').appendTo('#main').addClass('shadow');
    var $popup = $('<div>').appendTo($shadow).addClass('popup');

    $('.what-lies-beneath').on('click', function(event) {
        if ($(event.delegateTarget).attr('href') != '.')
            return;
        event.preventDefault();
        var $target = $(event.delegateTarget);
        var title = $target.html();
        var taxa = $.parseJSON($target.attr('data-taxa'));
        taxa.sort();
        $popup.empty();
        $('<h2/>').html(title).appendTo($popup);
        $.each(taxa, function(i, name) {
            $('<div/>').append($taxon_anchor(name)).appendTo($popup);
        });
        display_popup();
    });

    /* The popup can be dismissed with the mouse or keyboard. */

    var display_popup = function() {
        $shadow.css('display', 'block');
    }
    var dismiss_popup = function() {
        $shadow.css('display', '');
    };
    $shadow.on('click', dismiss_popup);
    $('body').on('keydown', function(event) {
        if ($shadow.css('display') === 'block') { // popup is active
            var c = event.which;
            if (c === 13 || c === 27 || c === 32) { // esc, enter, space
                dismiss_popup();
                return false;
            }
            // PageUp, PageDown, up arrow, down arrow - move the whole page
            if (c === 33 || c === 34 || c === 38 || c === 40) {
                return false;
            }
        }
    });

    /* Prevent popup scrolling from moving the page. */
    /* http://stackoverflow.com/questions/5802467/ */

    $shadow.on('mousewheel', function(e) {
        if ($(e.target).hasClass('shadow'))
            e.preventDefault();
    });

    $popup.on('mousewheel', function(e, d, deltaX, deltaY) {
        if (d > 0 && $(this).scrollTop() == 0)
            e.preventDefault();
        else if (d < 0 && $(this).scrollTop() ==
                 $(this).get(0).scrollHeight - $(this).innerHeight())
            e.preventDefault();
    });

    /* Clicking on a figure should pop it up without leaving the page. */

    $('.figure-link').each(function() {
        var $figure_link = $(this);

        var tooltip = new tooltip_js.Tooltip($figure_link, {
            content: $('<p>', {'class': 'glosstip'}).append(
                $('<img>', {src: $(this).attr('href'), height: 240}),
                $('<b>', {text: 'Figure ' + $(this).html() + '. '}),
                $(this).attr('data-caption'),
                '<br>(Click to view larger image)'
            )
        });

        $figure_link.on('click', function(event) {
            event.preventDefault();
            var $target = $(event.delegateTarget);
            if ($figure_link[0].timeout_id) {
                clearTimeout($figure_link[0].timeout_id);
                delete $figure_link[0].timeout_id;
            }
            tooltip.hide_tooltip();
            $popup.empty();
            $('<img>').attr('src', $target.attr('href')).appendTo($popup);
            display_popup();
        });
    });

    /* Download and display images, narrowing the taxa images to match
       the currently selected lead, and letting the user select the
       image type from a <select> box. */

    var title = $('[data-title]').eq(-1).attr('data-title');
    var slug = title.replace(/ /g, '-').toLowerCase();
    var images_url = API_URL + 'dkey-images/' + slug + '/';
    var plants = null;

    var install_image_types = function(image_types) {
        if (title === 'Key to the Families')
            // Botanists do not find images useful on the front page.
            return;
        var $selector = $('.image-type-selector').css('display', 'block');
        var $select = $selector.find('select');
        $.each(image_types, function(i, image_type) {
            var $option = $('<option>', {value: image_type, html: image_type});
            if (image_type == 'plant form')
                $option.attr('selected', 'selected');
            $select.append($option);
        });
        $select.on('change', show_appropriate_images);
    };

    var install_image_lists = function(image_lists) {
        var $grid = $('.plant-grid');
        plants = _.map(image_lists, function(item) {
            var $anchor =
                $('<a>', {
                    'class': 'plant',
                    'href': taxon_url(item.scientific_name)
                }).append(
                    $('<div>', {'class': 'plant-img-container'}),
                    $('<p>', {html: item.title})
                ).appendTo($grid);
            plantpreview_popup.connect($anchor, item.scientific_name);
            return {
                $div: $anchor,
                image_list: item.image_list,
                name: item.name,
                title: item.title
            };
        });
        show_appropriate_images();
    };

    var taxa_beneath_current_lead = function() {
        var $lead = $('#c' + active_id).parent().children('div.lead');
        if ($lead.length == 0) {
            var $wlb = $('#main > .what-lies-beneath');
        } else {
            var $wlb = $lead.find('.what-lies-beneath');
        }
        var current_taxa = $.parseJSON($wlb.attr('data-taxa'));
        return current_taxa;
    }

    var show_appropriate_images = function() {
        var image_type = $('.image-type-selector select').val();
        var current_taxa = taxa_beneath_current_lead();
        _.each(plants, function(plant) {
            var omit = ! _.contains(current_taxa, plant.name);
            plant.$div.toggleClass('omit', omit);
            if (omit)
                return;
            var matching_image = _.find(plant.image_list, function(image) {
                return image_type == image.image_type;
            });
            if (matching_image) {
                var content = $('<img>', {
                    'data-lazy-img-src': matching_image.image_url
                });
            } else {
                var content = '<div class="missing-image">';
            }
            plant.$div.find('.plant-img-container').html(content);
        });
        window.setTimeout(function() {lazy_images.load()}, 10);
    };

    $.getJSON(images_url, function(data) {
        install_image_types(data.image_types);
        install_image_lists(data.image_lists);
    });

    /* Front "Dichotomous Key to Families" page selectboxes for jumping
       to groups, families, and genera. */

    var family_jumpbox = $('.jumpbox')[0];
    var genus_jumpbox = $('.jumpbox')[1];

    var reset_select = function(element) {
        $(element).val('instructions');
    };

    $.getJSON('/api/hierarchy/', function(data) {
        var hierarchy = data.hierarchy;
        var family_names = _.pluck(hierarchy, 'family_name');
        var genus_names = _.flatten(_.pluck(hierarchy, 'genus_names'));

        family_names.sort();
        genus_names.sort();

        _.each(family_names, function(name) {
            $('<option>', {text: name}).appendTo(family_jumpbox);
        });
        _.each(genus_names, function(name) {
            $('<option>', {text: name}).appendTo(genus_jumpbox);
        });

        $(family_jumpbox).removeAttr('disabled');
        $(genus_jumpbox).removeAttr('disabled');
    });

    $('.groupbox select').on('mousedown keydown', function(event) {
        // Instead of letting the real select box drop down, toggle the <ul>.
        if (event.which == 9) {
            $('.groupbox ul').hide();
            return true;  // Let the Tab keystroke take us to the next field.
        } else {
            $('.groupbox select').focus();
            $('.groupbox ul').toggle();
            return false;
        }
    });

    $('.jumpbox').on('change', function(event) {
        var text = $(':selected', event.delegateTarget).html();
        reset_select(event.delegateTarget);
        if (text && ! text.match(/^jump/)) {
            window.location = taxon_url(text);
        }
    });

    /* Connect the couplet logic to our hash. */

    Hash.init(transition_to_hash);
})});
