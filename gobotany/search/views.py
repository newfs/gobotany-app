from haystack.views import SearchView

class GoBotanySearchView(SearchView):
    def __name__(self):
        return "GoBotanySearchView"

    def extra_context(self):
        extra = super(GoBotanySearchView, self).extra_context()

        # Supply a base for making results URLs.
        url_base = 'http%s://%s' % (
                's' if self.request.is_secure() else '',
                self.request.get_host())
        extra['url_base'] = url_base

        return extra

    def get_results(self):
        """When no results are found for multiple word searches, try
        searching without some of the words in order to be able to
        return something to the user rather than nothing. This is
        in the absence of partial word searches (user types a word
        and a partial word, and the partial word matches using a
        wildcard). Solr can be made to do partial word searches, but
        a quick fix was desired instead.
        """
        results = self.form.search()

        if len(results) == 0:
            # Query words come back "cleaned" from get_query().
            query_words = self.get_query().split(' ')
            if len(query_words) > 1:
                # Try queries that drop a word at a time off the end.
                for end_index in reversed(range(1, len(query_words))):
                    new_query = ' '.join(query_words[0:end_index])
                    self.form.cleaned_data['q'] = new_query
                    results = self.form.search()
                    if len(results) > 0:
                        # Found results for one of the words.
                        # Set our SearchView's query to the altered
                        # query, so the user can see the shortened
                        # search query that returned some results.
                        self.query = self.get_query()
                        break

        return results
