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

    # First create a mapping that, given a genus and paragraph number,
    # can tell us the species to which that paragraph refers.

    species_pages = list(models.Page.objects.filter(rank='species'))
    names = {}  # (genus_name, paragraph_int) -> species_name

    for page in species_pages:
        if page.title == 'Epimedium diphyllum':
            # This weird entry in the book contains no paragraph number.
            continue
        species_name = page.title
        genus_name = species_name.split()[0]
        match = re_paragraph_number.match(page.text)
        paragraph_int = int(match.group(1))
        key = (genus_name, paragraph_int)
        names[key] = species_name
        if debug and page.title == 'Huperzia appressa':
            print repr(page.text)
            print '-' * 72

    # Now we are prepared to embark on our rewrite: we snip off of each
    # dkey page's text any paragraphs describing hybrid species, improve
    # their paragraph titles so that they actually name the species that
    # form the hybrid, and then we save those paragraphs to the Hybrid
    # table so that they can appear on the species pages for both of
    # those species.

    for page in species_pages:
        species_name = page.title
        genus_name = species_name.split()[0]

        # These useless '</b><b>' sequences interfere with our RE.

        text = page.text.replace(u'</b><b>', u'')

        # Splitting on this RE generates a list that looks like:
        # [text, hybrid1_number1, hybrid1_number2, hybrid1_text,
        #        hybrid2_number1, hybrid2_number2, hybrid2_text, ...]

        text_and_hybrids = re_hybrid_subtitle.split(text)
        page.text = text_and_hybrids[0].strip()
        page.save()

        for i in range(1, len(text_and_hybrids), 3):
            number1, number2, text = text_and_hybrids[i:i+3]
            int1 = int(number1)
            int2 = int(number2)
            species1 = names[(genus_name, int1)]
            species2 = names[(genus_name, int2)]

            text = u'<b>' + text.rstrip()
            if text.endswith('</p>'):
                text = text[:-4]

            h = models.Hybrid()
            h.number1 = int1
            h.number2 = int2
            h.scientific_name1 = species1
            h.scientific_name2 = species2
            h.text = text.rstrip()
            h.save()

        if debug and page.title == 'Huperzia appressa':
            print page.text
            print '-' * 72


def abbr(scientific_name):
    """Abbreviate 'Genus epithet' to 'G. epithet'."""
    words = scientific_name.split()
    return u'{}. {}'.format(words[0][0], words[1])


if __name__ == '__main__':
    main()
