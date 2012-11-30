# -*- coding: utf-8 -*-
"""Command line tool to read dkey page texts, expanding cross-references.

Mainly, we discover paragraph headings like "2x3." and supplement them
with the actual names of species 2 and species 3 within that genus.

"""
from gobotany import settings
from django.core import management
management.setup_environ(settings)

import re
from django.db import transaction
from gobotany.dkey import models

debug = False
re_paragraph_number = re.compile(ur'^<p><b>(\d+)\.')
re_hybrid_subtitle = re.compile(ur'<p><b>(\d+)×(\d+)\.[\s\u202f]*')

@transaction.commit_on_success
def main():
    pages = list(models.Page.objects.filter(rank='species'))
    names = {}  # (genus_name, paragraph_int) -> species_name


    for page in pages:
        if page.title == 'Epimedium diphyllum':
            # This weird entry in the book contains no paragraph number.
            continue
        species_name = page.title
        genus_name, specific_name = species_name.split()
        match = re_paragraph_number.match(page.text)
        paragraph_int = int(match.group(1))
        key = (genus_name, paragraph_int)
        names[key] = '{}. {}'.format(genus_name[0], specific_name)
        if debug and page.title == 'Huperzia appressa':
            print repr(page.text)
            print '-' * 72

    def longer_hybrid_subtitle(match):
        """Add species names into X-by-Y hybrid paragraph titles."""
        if debug and page.title == 'Huperzia appressa':
            print repr(match.group(0))
            print '-' * 72
        int1 = int(match.group(1))
        int2 = int(match.group(2))
        return u'<p><b>{}×{}. <i>{}</i> × <i>{}</i> →'.format(
            match.group(1), match.group(2),
            names[(genus_name, int1)], names[(genus_name, int2)],
            )

    for page in pages:
        species_name = page.title
        genus_name = species_name.split()[0]
        text = page.text.replace(u'</b><b>', u'')
        text = re_hybrid_subtitle.sub(longer_hybrid_subtitle, text)
        page.text = text
        page.save()
        if debug and page.title == 'Huperzia appressa':
            print page.text
            print '-' * 72


if __name__ == '__main__':
    main()
