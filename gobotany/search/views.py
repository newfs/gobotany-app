"""The magic behind our search page."""

import re
from haystack.views import SearchView

class GoBotanySearchView(SearchView):
    __name__ = "GoBotanySearchView"

    def get_results(self):
        """When no results are found for multiple word searches, try
        searching without some of the words in order to be able to
        return something to the user rather than nothing. This is
        in the absence of partial word searches (user types a word
        and a partial word, and the partial word matches using a
        wildcard). Solr can be made to do partial word searches, but
        a quick fix was desired instead.
        """
        # Start by doing exactly what the base class does.

        queryset = self.form.search()

        # Fall back to less specific searches.

        if len(queryset) == 0:
            # Query words come back "cleaned" from get_query().
            query_words = self.get_query().split(' ')
            if len(query_words) > 1:
                # Try queries that drop a word at a time off the end.
                for end_index in reversed(range(1, len(query_words))):
                    new_query = ' '.join(query_words[0:end_index])
                    self.form.cleaned_data['q'] = new_query
                    queryset = self.form.search()
                    if len(queryset) > 0:
                        # Found results for one of the words.
                        # Set our SearchView's query to the altered
                        # query, so the user can see the shortened
                        # search query that returned some results.
                        self.query = self.get_query()
                        break

        # Privilege any result whose name is exactly what the user was
        # searching for, so that a search for "Acer" or "acer" returns
        # the Genus Acer first and foremost.

        words = re.findall(r'\w+', self.request.GET['q'])
        name = ' '.join(words).lower()
        queryset = queryset.filter_or(name__exact=name)

        return queryset
