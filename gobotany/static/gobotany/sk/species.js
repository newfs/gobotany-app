// Global declaration for JSLint (http://www.jslint.com/)
/*global dojo, dojox, dijit, gobotany, window, document */

dojo.provide('gobotany.sk.species');

dojo.require('dijit.TitlePane');
dojo.require('dijit.Tooltip');
dojo.require('dojo.cookie');
dojo.require('dojox.data.JsonRestStore');

dojo.require('gobotany.sk.glossary');

// Image info storage for images that appear on the species page.
gobotany.sk.species.images = [];

gobotany.sk.species.reopen_character_groups = function() {
    // Re-open any character groups that were open the last time the
    // user viewed this species page during this session.

    var open_character_groups = dojo.cookie('open_character_groups');
    if (open_character_groups !== undefined) {
        open_character_groups = open_character_groups.split(',');
        for (var i = 0; i < open_character_groups.length; i++) {
            var widget = dijit.byId(open_character_groups[i]);
            if (widget !== undefined) {
                if (!widget.open) {
                    widget.toggle();
                }
            }
        }
    }
};

gobotany.sk.species.init = function(scientific_name) {
    gobotany.sk.species.reopen_character_groups();

    // Make glossary highlights appear where appropriate throughout the page.
    var glossarizer = gobotany.sk.glossary.Glossarizer();
    dojo.query('#info p').forEach(function(node) {
        glossarizer.markup(node);
    });

    // Check for whether the stored filter-state cookie pertains to the
    // pile/results page for this plant. If so, replace the hyperlink href
    // for the pile/results page with the URL from the cookie in order to
    // persist filter state when the user clicks the link to go back.
    var last_plant_id_url = dojo.cookie('last_plant_id_url');
    var url_parts = window.location.toString().split('/');
    var pile_results_url = url_parts.slice(0, 6).join('/');
    if (last_plant_id_url.indexOf(pile_results_url) !== -1) {
        var link = dojo.byId('results-link');
        dojo.attr(link, 'href', last_plant_id_url);
    }

    // Decide whether to add a Go Back link based on whether the previous
    // URL was a pile/results page. If it was, add the link.
    var previous_url = '';
    if (document.referrer !== undefined) {
        previous_url = document.referrer;
    }

    // If the previous URL can be found as a substring in the current species
    // page URL, then the previous page was indeed a pile/results page.
    if (previous_url.length > 0) {
        if (window.location.href.indexOf(previous_url) > -1) {
            var species_node = dojo.query('#species')[0];
            if (species_node) {
                var back_link = dojo.create('a',
                    { innerHTML: '&lt; Back to plant identification' });
                dojo.attr(back_link, 'class', 'back');
                // The last plant identification URL should be the correct
                // destination for the link.
                dojo.attr(back_link, 'href', last_plant_id_url);
                dojo.place(back_link, species_node);
            }
        }
    }

};

gobotany.sk.species.persist_visibility = function(scientific_name) {
    // Save the state of character group boxes so they can be put back
    // the way the user left them after navigating away from the page
    // and then back.

    var group_ids = [];
    dojo.query('#species div.dijitTitlePane').forEach(function(div) {
        var group_id = dojo.attr(div, 'id');
        var widget = dijit.byId(group_id);
        if (widget.open) {
            group_ids.push(group_id);
        }
    });

    // The cookie is set with a default path to the species page, so the
    // persistence here will be per-page, i.e., not global across pages.
    // Also, this uses the default cookie expiration: end of session.
    dojo.cookie('open_character_groups', group_ids);
};
