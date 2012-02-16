from django.forms import widgets
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
from django.forms.util import flatatt

from autocomplete.views import autocomplete

AC_TEMPLATE = u'''
<div>
  <input type="hidden" name="%(name)s" id="id_hidden_%(name)s" value="%(hidden_value)s" />
  <input type="text" id="id_%(name)s" value="%(value)s" %(attrs)s />
  <script type="text/javascript">var %(var_name)s = new autocomplete("%(name)s", "%(url)s", %(force_selection)s);</script>
</div>
'''

class AutoCompleteWidget(widgets.Widget):

    AC_TEMPLATE = AC_TEMPLATE

    class Media:
        css = {'all':
            ("http://yui.yahooapis.com/2.6.0/build/autocomplete/assets/skins/sam/autocomplete.css",)
        }
        js = ('http://yui.yahooapis.com/combo'
              '?2.6.0/build/yahoo-dom-event/yahoo-dom-event.js'
              # decomment to enable animation.
              #'&2.6.0/build/animation/animation-min.js'
              '&2.6.0/build/connection/connection-min.js'
              '&2.6.0/build/datasource/datasource-min.js'
              '&2.6.0/build/autocomplete/autocomplete-min.js',
              'js/yui_autocomplete.js')

    def __init__(self, ac_name, force_selection=True, reverse_label=True,
                 view=autocomplete, attrs=None):
        super(AutoCompleteWidget, self).__init__(attrs)
        self.ac_name = ac_name
        self.force_selection = bool(force_selection)
        self.reverse_label = reverse_label
        self.view = view
    
    def render(self, name, value, attrs=None):
        var_name = 'ac_%s' % name.replace('-', '_')
        url = reverse(self.view, args=[self.ac_name])
        force_selection = ('false', 'true')[self.force_selection]
        if not value:
            value = hidden_value = u''
        elif self.reverse_label:
            hidden_value = force_unicode(value)
            value = self.view.reverse_label(self.ac_name, value)
        else:
            value = hidden_value = force_unicode(value)
        attrs = flatatt(self.build_attrs(attrs))
        return mark_safe(self.AC_TEMPLATE % locals())

