from django.http import HttpResponse
from django.db.models import Q
from django.utils import simplejson
from django.utils.encoding import smart_unicode


class AutoComplete(object):

    def __init__(self):
        self.settings = dict()

    def __call__(self, request, ac_name, query_param='q'):
        if not ac_name in self.settings:
            return self.not_found(request, ac_name)

        qs, fields, limit, key, label, auth = self.settings[ac_name]
        if auth and not request.user.is_authenticated():
            return self.forbidden(request, ac_name)
        query = request.GET.get(query_param, '')
        
        filter = Q()
        for field in fields:
            if not '__' in field:
                field = '%s__startswith' % field
            filter |= Q(**{field: query})
        
        qs = qs.filter(filter)[:limit]
        
        if isinstance(label, basestring):
            if key == 'pk':
                key = qs.model._meta.pk.attname
            result = list(qs.values_list(key, label))
        else:
            result = []
            for obj in qs:
                result.append((getattr(obj, key), label(obj)))
        return HttpResponse(simplejson.dumps(result),
                mimetype='application/json')

    def register(self, id, queryset, fields, limit=None, key='pk',
                 label=lambda obj: smart_unicode(obj), auth=False):
        self.settings[id] = (queryset, fields, limit, key, label, auth)

    def not_found(self, request, ac_name):
        return HttpResponse(status=404)

    def forbidden(self, request, ac_name):
        return HttpResponse(status=403)

    def reverse_label(self, ac_name, key_value):
        qs, fields, limit, key, label, auth = self.settings[ac_name]
        if key == label:
            return key_value
        if isinstance(label, basestring):
            qs = qs.values_list(label, flat=True)
        try:
            result = qs.get(**{key:key_value})
        except qs.model.DoesNotExist:
            return key_value
        if not callable(label):
            return result
        return label(result)


autocomplete = AutoComplete()
