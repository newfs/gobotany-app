def query_regex(plant_name):
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
            regex_word = '%s[%s]{%d,%d}%s' % (
                word[0],   # First character: an anchor
                interior_chars,    # Allow any, to handle transpositions
                interior_length,   # Allow typo with an extra character
                interior_length + 1,
                word[-1])  # Last character: another anchor
        else:
            regex_word = word
        regex_words.append(regex_word)

    # Allow ignoring hyphens, periods, and other non-word characters.
    query_regex = '\W+'.join(regex_words)

    return query_regex
