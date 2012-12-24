# -*- encoding: utf-8 -*-

from operator import itemgetter
from django.contrib import admin
from django.contrib.contenttypes import generic
from django.db import models as dbmodels
from django.template import Context, Template
from django import forms
from gobotany.core import models

from django.forms import Textarea

# View classes

class _Base(admin.ModelAdmin):

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(_Base, self).get_fieldsets(request, obj)

        for fieldset in fieldsets:
            options = fieldset[1]
            if options.get('description'):
                continue
            if not self.__doc__:
                continue
            prefix = '{% load gobotany_tags %}\n'
            template = Template(prefix + self.__doc__)
            options['description'] = template.render(Context({
                'obj': obj,
                'piles': models.Pile.objects,
                }))

        return fieldsets

    class Media:
        css = {'all': ('/static/admin_styles.css',)}

class GobotanyAdminBase(admin.ModelAdmin):

    class Media:
        css = {
            "all": ("/static/admin_styles.css",)
            }

class TaxonSynonymInline(admin.StackedInline):
    model = models.Synonym
    extra = 1

class TaxonCommonNameInline(admin.StackedInline):
    model = models.CommonName
    extra = 1

class TaxonLookalikeInline(admin.StackedInline):
    model = models.Lookalike
    extra = 1

class ContentImageInline(generic.GenericStackedInline):
    model = models.ContentImage
    extra = 1

#
# The fancy widget that presents character-value choices in the Django
# Admin interface goes through several stages during the lifetime of a
# particular taxon as that taxon is presented by the Admin interface.
#
# 1. Assume a taxon whose .id is 123.  The "initial value" of the HTML
#    form field, as set by TaxonAdminForm.__init__(), will be "d123",
#    which is a special hint to the TaxonFiltersWidget that it should
#    render the character values already stored in the database for the
#    taxon whose .id is 123.  Forms never come back from the web page
#    with a "d"-value included; that only happens if the initial value
#    is being used.
#
# 2. The TaxonFiltersWidget draws a series of form elements.  A single
#    hidden element specifies the value "f123", meaning "this is a real
#    form submission, for the taxon whose id == 123".  All of the other
#    elements are checkboxes whose value is the character_value.id of
#    the character value they are representing (thus these values look
#    simply like "1", "2", and so forth).
#
# 3. Should the form need to be re-displayed because of an error or an
#    illegal value somewhere on the Taxon page, the rendering function
#    of TaxonFiltersWidget will see the "f" in front of the Taxon ID
#    field and, instead of hitting the database to learn which character
#    values are currently set for the taxon, it will re-draw the form
#    using the selections that came in from the last version of the form
#    alongside the "f123" so that character value settings do not re-set
#    each time the user submits the form.
#
# 4. When the form is finally ready, TaxonAdminForm.save() swings into
#    action and makes sure that the filters selected for the species are
#    brought completely into line with the checkboxes that were set by
#    the user.  Note that a species being removed from a particular pile
#    necessarily results in that species losing ALL of the filters
#    related to that pile; if the species is later re-added to the pile,
#    it will start over again with all of the filters being blank!
#


filters_template = Template(u'''\
<br clear="left"><br>
<input type="hidden" name="{{ name }}" value="f{{ taxon_id }}">
{% for pile, clist in piles %}
  <h2>Pile {{ pile.name }}</h2>
  {% for character in clist %}
    <h3>
      {{ character.obj.short_name }} = {{ character.obj.name }}
      {% if character.obj.friendly_name %}
        = "{{ character.obj.friendly_name }}"
      {% endif %}
    </h3>
    {% if character.value_type == 'TEXT' and character.values %}
      {% for value in character.values %}
        <input type="checkbox" name="{{ name }}" value="{{ value.id }}"
         {% if value.checked %}checked{% endif %}> {{ value.text }}<br>
      {% endfor %}
    {% endif %}
    {% if character.value_type == 'LENGTH' %}
      Min–Max:
      <input name="{{ name }}__{{ pile.slug }}__{{ character.short_name }}__min"
             value="{{ character.min }}" size="7">
      –
      <input name="{{ name }}__{{ pile.slug }}__{{ character.short_name }}__max"
             value="{{ character.max }}" size="7">
      {% if character.unit != 'NA' %} {{ character.unit }} {% endif %}
    {% endif %}
  {% endfor %}
{% endfor %}
''')

class TaxonFiltersWidget(forms.CheckboxSelectMultiple):
    """Check box for each character value, grouped by pile."""

    def render(self, name, value, attrs=None):

        # value will either look like:
        # None when the add-species page is first added
        # [] when the add-species page is redisplay
        # ['d123'] for taxons that are being newly displayed
        # ['f123', '37, '47', '782'] for taxons coming back from the form

        if not value:
            return u''

        value.sort()  # move the taxon ID to the end of the list
        id_field = value.pop()
        taxon_id = int(id_field.lstrip('df'))
        taxon = models.Taxon.objects.get(id=taxon_id)
        if id_field.startswith('d'):
            cv_ids = set( cv.id for cv in taxon.character_values.all() )
        else:
            cv_ids = set( int(cvid) for cvid in value )

        pilelist = []
        for pile in taxon.piles.order_by('name'):
            characterdict = {}

            # Pull pile values from the database.

            clist = list(pile.characters.all())
            cvlist = list(
                models.CharacterValue.objects.filter(character__in=clist)
                )
            for cv in cvlist:

                c = cv.character
                if c.id not in characterdict:
                    characterdict[c.id] = {
                        'short_name': c.short_name, 'obj': c,
                        'value_type': c.value_type, 'values': [],
                        'unit': c.unit,
                        }

                if c.value_type == 'TEXT':  # Multiple-choice value

                    if cv.friendly_text:
                        text = u'%s = %s' % (cv.value_str, cv.friendly_text)
                    else:
                        text = cv.value_str
                    characterdict[c.id]['values'].append({
                        'id': cv.id,
                        'text': text,
                        'checked': cv.id in cv_ids,
                        })

                elif c.value_type == 'LENGTH':  # Length measurement

                    if cv.id in cv_ids:
                        characterdict[c.id]['min'] = (
                            cv.value_min if cv.value_min is not None else '')
                        characterdict[c.id]['max'] = (
                            cv.value_max if cv.value_max is not None else '')

            # Sort characters and character values for presentation.

            characterlist = sorted(characterdict.values(),
                                   key=itemgetter('short_name'))
            for characterdict in characterlist:
                characterdict['values'].sort(key=itemgetter('text'))

            pilelist.append((pile, characterlist))

        return filters_template.render(Context({
            'name': name,
            'piles': pilelist,
            'taxon_id': taxon_id,
            }))

class TaxonFiltersField(forms.MultipleChoiceField):
    widget = TaxonFiltersWidget

    def valid_value(self, value):
        """Each value should look like 'd123', 'f123', or '123'."""
        int(value.lstrip('df'))
        return True

class TaxonAdminForm(forms.ModelForm):
    filters = TaxonFiltersField(required=False)

    class Meta:
        model = models.Taxon

    def __init__(self, *args, **kw):
        super(TaxonAdminForm, self).__init__(*args, **kw)
        instance = kw.get('instance')
        if instance is not None:
            self.initial['filters'] = ['d%d' % instance.id]

    def clean_filters(self):
        """Why check - how can the user screw up checkboxes?"""
        return self.cleaned_data['filters']

    def clean(self):
        data = self.cleaned_data

        # Does the scientific name match the genus?

        genus_name = data['scientific_name'].split()[0]
        if genus_name != data['genus'].name:
            raise forms.ValidationError(
                'The genus %r in the scientific name does not match the'
                ' genus %r that you have selected for this species'
                % (genus_name, data['genus']))

        # Is the genus in the family?

        if data['genus'].family.id != data['family'].id:
            raise forms.ValidationError(
                'The genus %r belongs to the family %r but you have instead'
                ' selected the family %r for this species'
                % (data['genus'], data['genus'].family, data['family']))

        # Return!

        return self.cleaned_data

    def save(self, commit=True):

        # Set character multiple-choice values.

        filters = self.cleaned_data['filters']

        if filters:  # can be blank if the species belongs to no piles
            filters.sort()
            taxon_id = int(filters.pop().lstrip('f'))  # the "f123" value
            cv_ids = set( int(v) for v in filters )
            taxon = models.Taxon.objects.get(id=taxon_id)

            # Do the existing values look good?  Remove the ones that aren't.

            for tcv in models.TaxonCharacterValue.objects.filter(taxon=taxon):
                cv_id = tcv.character_value.id
                if cv_id in cv_ids:
                    cv_ids.remove(cv_id)  # does not need to be added to db
                else:
                    tcv.delete()  # needs to be removed from db

            # Add every value that is not already in the database.

            for cv_id in cv_ids:
                cv = models.CharacterValue.objects.get(id=cv_id)
                models.TaxonCharacterValue.objects.create(
                    taxon=taxon, character_value=cv)

        # Save everything else normally.

        return super(TaxonAdminForm, self).save(commit=commit)

        # NOTE: the above loop removes *all* length character values
        # from the species, because its logic says "remove each CV that
        # is not in the list of multiple-choice selections".  And this
        # form does not have access to the length text fields anyway,
        # since the "cleaned" data removes all fields not mentioned in
        # this form's list of fields - and we do not list specific
        # fields like "filters_spore_diameter_ly_max" but instead
        # generate and process them on-the-fly.

        # So length measures are reinstated in TaxonAdmin.save_model().


class TaxonAdmin(GobotanyAdminBase):
    inlines = [
        TaxonSynonymInline, TaxonCommonNameInline,
        TaxonLookalikeInline, ContentImageInline,
        ]
    #exclude = ('character_values',)
    filter_horizontal = ('piles',)
    form = TaxonAdminForm
    # XXX: Cannot filter on a reverse relation in Django 1.2
    list_filter = ('family',)
    #readonly_fields = ('scientific_name',)
    search_fields = ('scientific_name', 'piles__name', 'piles__friendly_name')

    def save_model(self, request, obj, form, change):

        this_is_an_add = obj.id is None

        # Save the object.

        super(TaxonAdmin, self).save_model(request, obj, form, change)

        # If this is a new species, we go ahead and add it to the
        # admin's partner sites.

        if this_is_an_add:
            user = request.user
            for partner in models.PartnerSite.objects.filter(users=user):
                models.PartnerSpecies(species=obj, partner=partner).save()

        # Save length ranges.

        names = set( name[:-5] for name in request.POST
                     if name.startswith('filters__')
                     and (name.endswith('__min') or name.endswith('__max')) )

        for name in names:
            x, pile_slug, character_name = name.split('__')
            pile = models.Pile.objects.get(slug=pile_slug)
            pile_characters = list(pile.characters.all())
            pile_cv_ids = set(
                cv.id for cv in
                models.CharacterValue.filter(character__in=pile_characters)
                )

            min_str = request.POST.get(name + '__min')
            max_str = request.POST.get(name + '__max')
            try:
                value_min = float(min_str or '')
            except ValueError:
                value_min = None
            try:
                value_max = float(max_str or '')
            except ValueError:
                value_max = None

            if value_min is None and value_max is None:
                continue

            c = models.Character.objects.get(short_name=character_name)
            cvs = models.CharacterValue.objects.filter(
                character=c, value_min=value_min, value_max=value_max).all()
            cvs = [ cv for cv in cvs if cv.id in pile_cv_ids ]
            if not cvs:
                # There is not already a character value with this
                # particular min and max?  Then create one!
                cv = models.CharacterValue.objects.create(
                    value_min=value_min, value_max=value_max, character=c,
                    )
                pile.character_values.add(cv)
                cvs = [ cv ]
            models.TaxonCharacterValue.objects.create(
                taxon=obj, character_value=cvs[0])

    # def formfield_for_manytomany(self, db_field, request, **kwargs):
    #     if db_field.name == 'character_values':
    #         pass #return TaxonCharacterValuesField()
    #     s = super(TaxonAdmin, self)
    #     return s.formfield_for_manytomany(db_field, request, **kwargs)

class PileDefaultFiltersForm(forms.ModelForm):
    class Meta:
        model = models.Pile.plant_preview_characters.through
    list_display = ('character')

class PilePlantPreviewCharactersForm(forms.ModelForm):
    class Meta:
        model = models.Pile.plant_preview_characters.through
    list_display = ('character')

class PilePlantPreviewCharactersInline(admin.StackedInline):
    model = models.Pile.plant_preview_characters.through
    form = PilePlantPreviewCharactersForm
    extra = 1

class PileGroupAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("slug",)}

class PileAdmin(GobotanyAdminBase):
    search_fields = ('name',)
    filter_horizontal = ('species',)
    inlines = [PilePlantPreviewCharactersInline]


class GlossaryTermAdmin(GobotanyAdminBase):
    list_display = ('term', 'lay_definition', 'visible')
    search_fields = ('term', 'lay_definition', 'question_text')
    ordering = ('term',)
    list_filter = ('visible',)


# This is the frontier between classes that have been vetted for
# acceptable semantics and performance (the ones below this comment),
# and those that have not (above).


class CharacterValuesInline(admin.TabularInline):
    model = models.CharacterValue
    extra = 0
    fields = ('value_str', 'friendly_text', 'image')
    formfield_overrides = {
        dbmodels.TextField: {'widget': Textarea(attrs={'rows':4})},
        }

    def queryset(self, request):
        """Only show character values for text-type characters."""
        qs = super(CharacterValuesInline, self).queryset(request)
        qs = qs.filter(character__value_type=u'TEXT')
        return qs

class CharacterAdmin(_Base):
    """

    <p>
    A “character” is a plant characteristic
    that users can employ to filter their plant selection
    in the Simple Key and Full Key.
    Once a character has been created,
    the “edit page” for that character can be visited
    to assign each plant in the database
    can be given a  value for a given character.
    </p>
    <p>
    A character with a “Value type” of “Length” only needs
    to specify its unit of measurement,
    while a character that is “Textual” offers a set of pre-defined
    multiple choice options that should be specified
    down at the bottom of this form
    as a list of “Character values.”
    </p>

    {% if obj.pile %}
    <p>
    You can edit the value of this character
    for all of the plants in its pile here:<br>
    <a href="/edit/cv/{{ obj.pile.slug }}/{{ obj.short_name }}/"
            >/edit/cv/{{ obj.pile.slug }}/{{ obj.short_name }}/</a>
    </p>
    {% else %}
    <p>
    You can edit the value of this character
    for the plants in each pile of the Simple Key:
    </p>
    <p>
    {% for pile in piles.all %}
    {{ pile.name }} —
    <a href="/edit/cv/{{ pile.slug }}/{{ obj.short_name }}/"
            >/edit/cv/{{ pile.slug }}/{{ obj.short_name }}/</a><br>
    {% endfor %}
    </p>
    {% endif %}

    """
    list_display = ('short_name', 'character_group', 'ease_of_observability',)
    list_filter = ('character_group',)
    search_fields = ('short_name', 'name',)
    inlines = [CharacterValuesInline]

    class Media:
        css = {'all' : ('css/admin_hide_original.css',)}


class FamilyAdmin(_Base):
    """

    <p>
    Each Family object represents a taxonomic genus,
    and makes a “family page” available where users
    can learn more about a particular family and its species.
    To assign a species to a family or remove it later,
    visit the species here in the admin interface
    and use its Family pull-down menu.
    </p>

    {% if obj %}
    <p>
    You can visit the Go Botany page for this family here:<br>
    <a href="{{ obj|url }}">{{ obj|url }}</a>
    </p>
    {% endif %}

    """
    search_fields = ('name', 'common_name')


class GenusAdmin(_Base):
    """

    <p>
    Each Genus object represents a taxonomic genus,
    and makes a “genus page” available where users
    can learn more about a particular genus and its species.
    To assign a species to a genus or remove it later,
    visit the species here in the admin interface
    and use its Genus pull-down menu.
    </p>

    {% if obj %}
    <p>
    You can visit the Go Botany page for this genus here:<br>
    <a href="{{ obj|url }}">{{ obj|url }}</a>
    </p>
    {% endif %}

    """
    search_fields = ('name', 'common_name')


class PartnerSiteAdmin(_Base):
    """

    <p>
    Each “partner site” entry represents an <b>allied organization</b>
    for whom we are hosting a customized copy of the Go Botany application.
    While their pages will display data
    from the same taxon and character tables that drive our own pages,
    they can be specific in choosing which <b>species</b> appear
    in their own versions of the Simple Key,
    and for each species they choose
    they can also provide a <b>blurb</b> to display
    at the top of their own site's copy of the Species Page.
    </p>

    <p>
    Using the filter below, you can assign <b>users</b> to a partner,
    in case you want to give their staff one or more Django admin accounts
    and let them log in here to edit their own species list or data.
    </p>

    """
    filter_horizontal = ('users',)

    # TODO: assignment of species to partner
    # an "inline" is too slow
    # a "list_display" cannot handle m2m
    # "filter_horizontal" complains because m2m has extra fields


# Registrations

admin.site.register(models.Parameter)
admin.site.register(models.ContentImage)
admin.site.register(models.HomePageImage)
admin.site.register(models.ImageType)
admin.site.register(models.PileGroup, PileGroupAdmin)
admin.site.register(models.Pile, PileAdmin)
admin.site.register(models.GlossaryTerm, GlossaryTermAdmin)
admin.site.register(models.CharacterGroup)
admin.site.register(models.Taxon, TaxonAdmin)

admin.site.register(models.Character, CharacterAdmin)
admin.site.register(models.Family, FamilyAdmin)
admin.site.register(models.Genus, GenusAdmin)
admin.site.register(models.PartnerSite, PartnerSiteAdmin)
