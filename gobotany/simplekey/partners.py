# partners.py: Module for helping customize the Simple Key for partner sites.

from gobotany.settings import MONTSHIRE_HOSTNAME_SUBSTRING

class MainSite(object):
    # Base class for the main Go-Botany Simple Key site.

    def __init__(self, host):
        self.host = host

    def index_page_main_heading(self):
        return 'Plant Identifier: Getting Started'


class MontshireSite(MainSite):
    # Subclass for the Montshire Museum's Simple Key site.

    def index_page_main_heading(self):
        return 'Montshire %s' % MainSite.index_page_main_heading(self)


# From a view, call this factory function, passing the HttpRequest object, to
# get the appropriate site object.

def get_site(request):
    host = request.get_host()
    if (host.find(MONTSHIRE_HOSTNAME_SUBSTRING) > -1):
        return MontshireSite(host)
    else:
        return MainSite(host)
