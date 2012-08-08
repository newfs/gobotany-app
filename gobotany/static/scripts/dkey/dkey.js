define([
    'bridge/jquery',
    'bridge/jquery.mousewheel',
    'util/Hash'
], function($, ignore, Hash) {$(document).ready(function() {

    var couplet_rank = $('body').attr('data-couplet-rank');
    var couplet_title = $('body').attr('data-couplet-title');

    // Where to direct RPC requests for lists of images.

    var gobotany_host = 'quiet-wind-6510.herokuapp.com';

    // Rewrite couplet IDs so that #-links will no longer match.

    $('.couplet').each(function(i, ul) {
        var id = $(ul).attr('id');
        if (id)
            $(ul).attr('id', 'c' + id);  // make 'c2' into 'cc2'
    });

    // Visiting particular couplets.

    var focus_on_one_couplet = function(new_hash, is_initial) {

        var duration = is_initial ? 0 : 200;
        if (!is_initial)
            $('.couplet:animated').stop();

        /* First, reset all state. */

        $all_couplets = $('.couplet');
        $all_leads = $('.lead');

        $all_couplets.removeClass('active');
        $all_leads.removeClass('chosen');

        /* The hash determines what we display. */

        if (new_hash === 'all') {
            var $couplet = null;
            var leads_to_show = $all_leads.toArray();
        } else {
            var $couplet = $(new_hash ? '#c' + new_hash : '.couplets');
            var $parent_leads = $couplet.parents('li').children('.lead');

            $couplet.addClass('active');
            $parent_leads.addClass('chosen');

            var leads_to_show = $couplet.parents('.couplet').andSelf()
                .children('li').children('.lead').toArray();
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

        /* Scroll to the target couplet; this animate() call has to
           follow the slideUp() and slideDown() calls above, to make the
           scrolling land at the right place. */

        if (!is_initial && $couplet !== null) {
            $('html, body').animate({
                scrollTop: $couplet.offset().top
            }, duration);
        }

        /* Enable or disable the "show all" button. */

        if (new_hash === 'all') {
            $('.show-all-button').addClass('disabled').removeAttr('href');
        } else {
            $('.show-all-button').removeClass('disabled').attr('href', '#all');
        }
    }

    /* Connect the couplet logic to our hash. */

    Hash.init(focus_on_one_couplet);

    /* Clicking on "See list of 7 genera in 1b" should display them. */

    var $shadow = $('<div>').appendTo('body').addClass('shadow');
    var $popup = $('<div>').appendTo($shadow).addClass('popup');

    $('.what-lies-beneath').on('click', function(event) {
        if ($(event.delegateTarget).attr('href') != '.')
            return;
        event.preventDefault();
        var $target = $(event.delegateTarget);
        var title = $target.html();
        var taxa = $target.attr('data-taxa').split(',');
        var tag = title.match(/species|genera/) ? '<i>' : '<span>';
        taxa.sort();
        $popup.empty();
        $('<h2>').html(title).appendTo($popup);
        $.each(taxa, function(i, name) {
            var url = '/' + name.replace(' ', '-') + '/';
            $('<div>').append(
                $('<a>').attr('href', url).append($(tag).html(name))
            ).appendTo($popup);
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
            var $div = $('.taxon-images');
            $.each(data.images, function(i, info) {
                $('<img>').attr('src', info.thumb_url).appendTo($div);
            });
        });
    }

    /* Front page selectboxes for jumping to families and genera. */

    $('.jumpbox').on('change', function(event) {
        console.log(event);
        console.log($(':selected', event.delegateTarget));
        var jumpto = $(':selected', event.delegateTarget).html();
        if (jumpto && ! jumpto.match(/^Jump/)) {
            window.location = '/dkey/' + jumpto + '/';
        }
    });
})});
