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

