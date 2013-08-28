import re

def query_regex(plant_name, anchor_at_start=False, anchor_at_end=False):
    """Return a regular expression for matching a query (plant name, etc.),
    allowing for some typos and punctuation differences. This is for use in
    various auto-suggest and other web service calls.
    """
    # Remove any extra spaces in the query.
    query = ' '.join(plant_name.split())

    # Split the words and create regular expressions for typo matching:
    # - Interior transpositions: pylmouth rose-gentian, plymouth rsoe-gentian
    # - An extra character: plymoutth rose-gentian
    # - A missing duplicate character: sabatia kenedyana (missing an 'n')
    regex_words = []
    words = query.split()
    for word in words:
        if len(word) > 2:
            interior_length = len(word[1:-1])
            interior_chars = ''.join(set(list(word[1:-1])))   # Unique chars.

            # Allow omitting an interior apostrophe if the word has one.
            interior_chars += '\''

            regex_word = '%s[%s]{%d,%d}%s' % (
                re.escape(word[0]),   # First character: an anchor
                re.escape(interior_chars),  # Allow any: handle transpositions
                interior_length - 1,   # Allow typo with an extra character
                interior_length + 1,
                re.escape(word[-1]))  # Last character: another anchor
        else:
            regex_word = word
        regex_words.append(regex_word)

    # Allow ignoring hyphens, periods, and other non-word characters.
    query_regex = '\W+'.join(regex_words)

    # Anchor the regular expression at the ends of the string if requested.
    if anchor_at_start:
        query_regex = '^%s' % query_regex
    if anchor_at_end:
        query_regex = '%s$' % query_regex

    return query_regex
