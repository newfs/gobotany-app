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

    var is_species = function(name) {
        return name.indexOf(' ') != -1;
    };

    var taxon_url = function(name) {
        var name = name.toLowerCase();
        if (is_species(name))
            return '/species/' + name.replace(' ', '/') + '/?key=dichotomous';
        else
            return '/dkey/' + name.toLowerCase() + '/';
    };

    var $taxon_anchor = function(name) {
        var url = taxon_url(name);
        if (is_species(name))
            return $('<a/>', {'href': url}).append($('<i/>', {'text': name}));
        else
            return $('<a/>', {'href': url, 'text': name});
    };

    /* Visiting particular couplets. */

    $('.lead .button').each(function() {
        $(this).attr('original-text', $(this).text());
    });

    var focus_on_one_couplet = function(new_hash, is_initial) {

        var duration = is_initial ? 0 : 200;
        if (!is_initial)
            $('.couplet:animated').stop();

        /* First, reset all state. */

        $all_couplets = $('.couplet');
        $all_leads = $('.lead');
        $all_buttons = $all_leads.find('.button');

        $all_couplets.removeClass('active');
        $all_leads.removeClass('chosen');
        $all_leads.removeClass('go-back');
        $all_buttons.each(function() {
            $(this).text($(this).attr('original-text'));
        });

        /* The hash determines what we display. */

        if (new_hash === 'all') {
            var $couplet = null;
            var leads_to_show = $all_leads.toArray();
        } else {
            var $couplet = $(new_hash ? '#c' + new_hash : '.couplets');
            var $parent_leads = $couplet.parents('li').children('.lead');

            $couplet.addClass('active');
            $parent_leads.addClass('chosen');

            var $active_leads = $couplet.children('li').children('.lead');
            var $ancestor_leads = $couplet.parents('li').children('.lead');
            var leads_to_show = $active_leads.toArray().concat(
                $ancestor_leads.toArray());

            $ancestor_leads.find('.button').text('GO BACK');
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
        if (new_hash === 'all') {
            button.html('Show First Couplet').attr('href', '#');
        } else {
            button.html('Show All Couplets').attr('href', '#all');
        }
    }

    /* Connect the couplet logic to our hash. */

    Hash.init(focus_on_one_couplet);

    /* Clicking on "See list of 7 genera in 1b" should display them. */

    var $shadow = $('<div>').appendTo('#main').addClass('shadow');
    var $popup = $('<div>').appendTo($shadow).addClass('popup');

    $('.what-lies-beneath').on('click', function(event) {
        if ($(event.delegateTarget).attr('href') != '.')
            return;
        event.preventDefault();
        var $target = $(event.delegateTarget);
        var title = $target.html();
        var taxa = $target.attr('data-taxa').split(',');
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

    $('.jumpbox').on('change', function(event) {
        var text = $(':selected', event.delegateTarget).html();
        reset_select(event.delegateTarget);
        if (text && ! text.match(/^jump/)) {
            window.location = taxon_url(text);
        }
    });
})});
