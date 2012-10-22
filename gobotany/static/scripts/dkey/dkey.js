define([
    'bridge/jquery',
    'bridge/jquery.mousewheel',
    'bridge/underscore',
    'lib/Hash',
    'simplekey/glossarize',
    'util/lazy_images'
], function(
    $, ignore, _, Hash, glossarize, lazy_images
) {$(document).ready(function() {

    var couplet_rank = $('body').attr('data-couplet-rank');
    var couplet_title = $('body').attr('data-couplet-title');

    /* Enable lazy image loading. */

    lazy_images.start();

    /* Glossarize lead texts. */

    glossarize($('.couplets .lead'));

    /* Where to direct RPC requests for lists of images. */

    var gobotany_host = 'quiet-wind-6510.herokuapp.com';

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
            return '/species/' + name.replace(' ', '/') + '/?key=dichotomous';
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

    $('.lead .button').each(function() {
        $(this).attr('original-text', $(this).text());
    });

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
    }

    $('.lead .button').on('click', function() {
        if ($(this).text() === go_back_text) {
            var raw_active_id = $(this).closest('.couplet').attr('id');
            var new_active_id = raw_active_id.replace('cc', 'c');
            Hash.go(new_active_id + ',' + bottom_id);
            return false;
        }
    });

    /* Connect the couplet logic to our hash. */

    Hash.init(transition_to_hash);

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

    $('.figure-link').on('click', function(event) {
        event.preventDefault();
        var $target = $(event.delegateTarget);
        $popup.empty();
        $('<img>').attr('src', $target.attr('href')).appendTo($popup);
        display_popup();
    });

    /* Load images for the user to enjoy. */

    var set_image_type = function() {
        var type = $('.image-type-selector select').val();
        $('.taxon-images figure').each(function(i, figure) {
            var show = $(figure).attr('data-image-type') == type;
            $(figure).css('display', show ? 'inline-block' : 'none');
        });
        lazy_images.load();
    };

    if (couplet_rank == 'family') {
        var family = couplet_title.split(/ /).pop().toLowerCase();
        var urlpath = '/api/families/' + family + '/';
    } else if (couplet_rank == 'genus') {
        var genus = couplet_title.split(/ /).pop().toLowerCase();
        var urlpath = '/api/genera/' + genus + '/';
    } else if (couplet_rank == 'species') {
        var name = couplet_title.replace(' ', '%20');
        var urlpath = '/api/taxa/' + name + '/';
    }
    if (urlpath) {
        var url = 'http://' + gobotany_host + urlpath;
        $.getJSON(url, function(data) {
            var types = [];
            var $div = $('.taxon-images');
            $.each(data.images, function(i, info) {
                types.push(info.type);
                var species = info.title.split(':')[0];
                $('<figure/>', {
                    'data-image-type': info.type,
                    'css': {'display': 'none'}
                }).append(
                    $('<img/>').attr('data-lazy-img-src', info.thumb_url),
                    $taxon_anchor(species)
                ).appendTo($div);
            });
            types = _.uniq(types);
            types.sort();

            var $selector = $('.image-type-selector');
            var $select = $selector.find('select');
            $.each(types, function(i, type) {
                var option = $('<option>').attr('value', type).html(type);
                if (type == 'plant form') option.attr('selected', 'selected');
                $select.append(option);
            });
            $selector.css('display', 'block');

            set_image_type();
            $select.on('change', set_image_type);
        });
    }

    /* Front "Dichotomous Key to Families" page selectboxes for jumping
       to groups, families, and genera. */

    var reset_select = function(element) {
        $(element).val('instructions');
    };

    $('.groupbox select').on('mousedown', function(event) {
        // Instead of letting the real select box drop down, show the <ul>.
        $('.groupbox ul').toggle();
        return false;
    });

    $('.jumpbox').on('change', function(event) {
        var text = $(':selected', event.delegateTarget).html();
        reset_select(event.delegateTarget);
        if (text && ! text.match(/^jump/)) {
            window.location = taxon_url(text);
        }
    });
})});
