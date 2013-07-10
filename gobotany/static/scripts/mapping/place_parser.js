define([
    'bridge/jquery',
], function ($) {

    // Constructor
    function PlaceParser() {
        this.EXCLUDE_WORDS = ['about', 'above', 'around', 'behind', 'below',
            'beneath', 'between', 'by', 'just', 'near', 'next', 'not',
            'over', 'past', 'through', 'under'];
    };

    PlaceParser.prototype._has_initial_cap_words = function (text) {
        return /[A-Z]+/g.test(text);
    };

    PlaceParser.prototype.parse = function (text) {
        var i;
        var possible_places = [];
        var has_initial_cap_words = this._has_initial_cap_words(text);

        if (has_initial_cap_words) {
            var matches = text.match(/(([A-Z][a-z]{1,}[\s\.]{0,}){1,})/g);
            for (i = 0; i < matches.length; i++) {
                possible_places.push(matches[i]);
            }
        }
        else {
            // If there are no uppercase words and the number of words
            // is reasonably small, try geocoding the whole string.
            // This would handle cases where people just jot a lowercase
            // place name into the Location Notes field.
            var MAX_WORDS = 5;
            var words = text.split(' ');
            if (words.length <= MAX_WORDS) {
                possible_places.push(text);
            }
        }

        // Exclude certain words if they appear at the start of a possible
        // place name, which may be the capitalized first word of a sentence.
        for (i = 0; i < possible_places.length; i++) {
            var place = possible_places[i];
            var words = place.split(' ');
            if ($.inArray(words[0].toLowerCase(), this.EXCLUDE_WORDS) > -1) {
                // Get rid of the word to be excluded.
                words.shift();
                possible_places[i] = words.join(' ');
            }
        }

        return possible_places;
    };

    // Return the constructor function.
    return PlaceParser;
});
