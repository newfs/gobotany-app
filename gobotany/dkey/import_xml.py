# -*- coding: utf-8 -*-

import logging
import re
from lxml import etree

from gobotany import settings
from django.core import management
management.setup_environ(settings)

from django.db import connection, transaction
from gobotany.dkey import models

# Couplet creation shortcuts, that work because during the import we
# never let Couplet objects that we have created expire out of memory.

class Info(object):
    """Objects created to represent Flora Novae Angliae."""

    def __init__(self):
        self.pages = {}
        self.leads = []

    def get_or_create_page(self, title):
        page = self.pages.get(title)
        if page is not None:
            return page
        page = models.Page()
        page.title = title
        page.save()
        self.pages[title] = page
        return page

    def get_page(self, title):
        return self.pages[title]

    def create_lead(self, page, parent=None, goto_page=None, goto_num=None):
        lead = models.Lead()
        lead.page = page
        lead.parent = parent
        if isinstance(goto_page, basestring):
            goto_page = self.get_or_create_page(goto_page)
        lead.goto_page = goto_page
        lead.goto_num = goto_num
        lead.save()
        self.leads.append(lead)
        return lead

# The import logic itself.

log = logging.getLogger('dkey')

level_tags = dict([ ('text_indent_%02d' % i, i) for i in range(1, 25) ])
level_tags['text_no_indent'] = 0

misspellings = {
    u'graveolenst': u'graveolens',
    u'ambrosioides': u'ambrosoides',
    u'Cuminun': u'Cuminum',
    u'depaupertata': u'depauperata',
    u'nodusus': u'nodosus',
    u'Plantanthera': u'Platanthera',
    u'Rubus parviflorus': u'Rubus parvifolius',
    }

def norm(u):
    """Normalize a string so it matches other strings in the document."""
    u = u.replace(u'‑', u'-').replace(u'\u202f', u' ')
    for k, v in misspellings.iteritems():
        if k in u:
            log.error('misspelling: "%s"' % k)
            u = u.replace(k, v)
    if u.endswith('arvens'):
        log.error('misspelling: "arvens"')
        u = u.replace(u'arvens', u'arvense')
    if u.endswith('morrowi'):
        log.error('misspelling: "morrowi"')
        u = u.replace(u'morrowi', u'morrowii')
    return u

re_number = re.compile('\d+')
re_genus_letter = re.compile(ur'\b([A-Z]\.)(<[^>]+>|)[ \n]+')

def p(text):
    return u'<p>{}</p>'.format(text)

def extract_html(x, skip=0, endskip=0):
    """Convert the xml children of `x` to html, skipping `skip` children."""
    s = x[skip-1].tail if skip else x.text
    for i in range(skip, len(x) - endskip):
        tag = x[i].tag
        text = x[i].text or u''
        tail = x[i].tail or u''
        tail0 = tail[0:1]
        space = ' ' if tail0.isalpha() or tail0 in '(' else ''

        if tag in (u'bold_L', u'light_var', u'more_or_less_sign'):
            s += u'%s%s%s' % (text, space, tail)
        elif tag == u'bold_ex':
            s += u'<i>%s</i>%s%s' % (text, space, tail)
        elif tag == u'bold_italic':
            s += u'<b><i>%s</i></b>%s%s' % (text, space, tail)
        elif tag == u'bold_sitations':
            s += u'%s%s%s' % (text, space, tail)
        elif tag in (u'bold_ssp', u'bold_var'):
            s += u'<b>%s</b>%s%s' % (text, space, tail)
        elif tag in u'designation_f':
            s += u'%s%s%s' % (text, space, tail)
        elif tag == u'distribution_character':
            for letter in text.split():
                s += u'<span class="distribution-character">%s</span>' % letter
            s += '%s%s' % (space, tail)
        elif tag == u'figure_reference':
            numbers = re_number.findall(text)
            for number in reversed(numbers):
                s += '<FIG-%s>' % number
            s += tail
        elif tag == u'fraction':
            s += u'<span class="fraction">%s</span>%s%s' % (
                text, space, tail)
        elif tag == u'italic':
            s += u'<i>%s</i>%s%s' % (text, space, tail)
        elif tag in (u'lead_number_letter', u'lead_number_letter_inner'):
            if i+1 < len(x) and x[i+1].tag.startswith('mult'):
                s += u'<b>%s</b>' % text
            else:
                s += u'<b>%s</b>%s%s' % (text, space, tail)
        elif tag == 'multiplication_sign_bold':
            s += u'<b>%s</b>' % text
        elif tag == u'small_caps':
            s += u'<small>%s</small>%s%s' % (text, space, tail)

        elif tag in (u'multiplication_sign_light',):
            s += text + space + tail.strip()
        elif tag in ('bullet',):
            s += text + tail
        elif tag in ('trailing_group_designation',
                     'trailing_genus_designation',):
            pass
        else:
            log.warn('unknown tag %s', tag)

    s = (s

         #.replace(u'–', u'–\u2060')    # tell n-dashes not to break
         # (disabled because Windows just displays a box for the \u2060)

         .replace(u' cm', u'\u00a0cm') # refuse to orphan units
         .replace(u' mm', u'\u00a0mm')
         .replace(u'\u2009cm', u'\u202fcm')
         .replace(u'\u2009mm', u'\u202fmm')
         )
    s = re_genus_letter.sub(ur'\1\2\u00a0', s) # "F. bar" non breaking space

    return s.strip()

# Detectors for various kinds of paragraph.

re_1_species = re.compile(r'^[Oo]nly (1|one) species')
lead_tags = ('lead_number_letter', 'lead_number_letter_inner')
species_tags = ('text_no_indent',
                'text_no_indent_description',
                'text_no_indent_no_leader')

def lead_number(x):
    if not (x.text or '').strip() and len(x) and x[0].tag in lead_tags:
        text = x[0].text.strip()
        if len(text) and text[0].isdigit() and text.endswith('.'):
            return text[:-1]
    return None

def is_lead(x):
    num = lead_number(x)
    return (num and num[-1].isalpha() and (
            x[0].tail.strip() or len(x) > 1 and x[1].text.strip()))

def is_species(x):
    num = lead_number(x)
    return (x.tag in species_tags and len(x) >= 2 and num and num.isdigit()
            and x[1].tag == 'bold_italic')

def is_discourse(x):
    return (
        not is_lead(x) and not is_species(x)
        and (x.tag in level_tags or x.tag in
             ('references', 'text_no_indent_description', 'text_no_indent',
              'text_no_indent_no_leader'))
        and not re_1_species.search(x.text)
        )

def is_empty(x):
    if not len(x) and not x.text.strip():
        return True
    return (len(x) == 1 and not x.text.strip()
            and not x[0].text.strip() and not x[0].tail.strip())

def remove_empty_elements(x):
    children = list(x)
    for element in children:
        remove_empty_elements(element)
        if (len(element) == 0
            and not (element.text or '').strip()
            and not (element.tail or '').strip()):
            x.remove(element)

# The main parser functions.  Which do not actually do any parsing; they
# really just iterate over what ElementTree returns to them.

def parse(filename):
    f = open(filename)
    try:
        root = etree.parse(f).getroot()
    finally:
        f.close()

    info = Info()

    # Delete empty elements, which are all over the place and cause lots
    # of problems.

    remove_empty_elements(root)

    # Parse every chapter.

    xchapters = root.findall('.//chapter')
    for xchapter in xchapters:
        parse_chapter(xchapter, info)

    # Find the figure captions.

    info.captions = {}
    xcaptions = root.find('.//caption_list').findall('caption')
    for i, xcaption in enumerate(xcaptions):
        n = i + 1
        assert xcaption[0].text == u'Fig.\u2009%03d\u2002' % n
        info.captions[n] = extract_html(xcaption, skip=1)

    # All done.

    return info

# The big chapter parser.

def parse_chapter(xchapter, info):
    most_recent_taxon = None  # used to label Groups more specifically
    genus_name = None  # used to expand abbreviated genus names
    species_comes_next = False  # when we know it's a species, darn it
    xchildren = list(xchapter)
    xtitle = xchildren[0]
    assert xtitle.tag == 'chapter_title', repr(xtitle.tag)
    title = xtitle.text.strip()
    log.info('* %s', title)

    # The initial Key to the Families chapter starts right off with a
    # series of couplets; subsequent chapters have headings instead, so
    # we can skip on down to the section-processing logic below.

    if title == u'Key to the Families':
        page = info.get_or_create_page(title)
        page.rank = 'top'
        i = parse_section(info, page, None, xchildren, 1)
    else:
        i = 1

    # As long as there are sections remaining, process them.

    while i < len(xchildren):
        child = xchildren[i]
        tag = child.tag

        if species_comes_next or is_species(child):

            # It's a species!

            fix_typo3(xchildren, i)

            if species_comes_next:
                name = child.find('bold_italic').text.strip()
            else:
                name = leading_species_name(child)

            species_comes_next = False

            if name is None:
                log.warn('cannot make a species out of <%s>' % tag)
                i += 1
                continue
            log.info('  * %s', name)
            page = info.get_or_create_page(name)
            page.rank = 'species'
            page.text += p(extract_html(child, skip=0))
            i += 1
            while i < len(xchildren) and (is_discourse(xchildren[i])
                or is_lead(xchildren[i]) and not is_species(xchildren[i])):
                # (xchildren[i].tag in (
                # 'text_no_indent_description',
                # 'text_no_indent_no_leader',
                # ) or xchildren[i].tag in level_tags  #ack! really?
                #):
                log.info('    species descriptive <%s>', xchildren[i].tag)
                page.text += p(extract_html(xchildren[i]))
                i += 1
            continue

        heading = norm(child.text.strip())
        if not heading:
            log.warn('empty <%s>' % child.tag)
            i += 1
            continue

        log.info(' * %s <%s>', heading, child.tag)

        if tag == 'head_1_group':
            rank = 'group'
            genus_name = None
            prefix = None
        elif tag == 'head_1':
            rank = 'family'
            genus_name = None
            most_recent_taxon = heading
            prefix = None
        elif tag == 'head_2':
            rank = 'genus'
            genus_name = heading
            most_recent_taxon = heading
            prefix = genus_name
        elif tag == 'head_3_group':
            rank = 'subgroup'
            # 'Group 1' -> 'Asteraceae Group 1'
            heading = most_recent_taxon + ' ' + heading
            if genus_name == 'Carex':
                prefix = 'Tribe'
            else:
                prefix = None
        elif tag == 'head_3':
            rank = 'tribe'
            # 'Acrocystis' -> 'tribe Acrocystis'
            heading = 'Tribe ' + heading
            prefix = genus_name
        else:
            log.error('truncating chapter, unrecognized tag: %s', tag)
            break

        page = info.get_or_create_page(heading)
        page.rank = rank
        page.chapter = title
        i += 1

        # Special case a genus with only one species. (Epimedium)

        if rank == 'genus' and xchildren[i].tag == 'text_indent_02':
            name = xchildren[i][0].text.strip()
            info.create_lead(page, goto_page=name)
            # we do NOT advance `i` so the species will be processed next
            species_comes_next = True
            continue

        # Then we grab the following paragraphs as part of this
        # page's description.

        while is_discourse(xchildren[i]):
            log.info('    descriptive <%s>', xchildren[i].tag)
            page.text += p(extract_html(xchildren[i]))
            i += 1

        # Special case another style of genus with only one species.

        if rank == 'genus' and genus_name in ('Convolvulus', 'Rhodotypos'):
            name = xchildren[i].find('bold_italic').text.strip()
            info.create_lead(page, goto_page=name)
            # we do NOT advance `i` so the species will be processed next
            species_comes_next = True
            continue

        # Assume that we must be looking at a heading.

        if i >= len(xchildren):
            pass
        elif xchildren[i].tag in level_tags:
            i = parse_section(info, page, prefix, xchildren, i)
        elif page.rank == 'family' and xchildren[i].tag == 'head_2':
            # the family has only one genus
            next_heading = xchildren[i].text.strip()
            info.create_lead(page, goto_page=next_heading)
            # we do NOT advance `i` so the heading will be processed next
        elif page.rank in ('tribe', 'subgroup') \
                and re_1_species.search(xchildren[i].text):
            name = trailing_taxon_name(genus_name, xchildren[i])
            info.create_lead(page, goto_page=name)
            i += 1
        elif page.rank == 'genus' and xchildren[i].tag == \
                'text_no_indent_no_leader':
            name = leading_species_name(xchildren[i])
            info.create_lead(page, goto_page=name)
            # we do NOT advance `i` so the species will be processed next

        elif xchildren[i].tag == 'head_4':
            # alternate keys, like 'Key for carpellate reproductive material'
            while i < len(xchildren) and xchildren[i].tag == 'head_4':
                title = ' '.join((most_recent_taxon,
                                  xchildren[i].text.strip().lower()))
                log.info(' ** %s', title)
                sub_page = info.get_or_create_page(title)
                sub_page.rank = 'subkey'
                info.create_lead(page, goto_page=sub_page)
                i = parse_section(info, sub_page, prefix, xchildren, i + 1)
        else:
            log.error('not sure what to do with <%s>' % xchildren[i].tag)


def leading_species_name(x):
    """Given a <text_no_indent_no_leader>, return its species name."""
    assert x[0].tag == 'lead_number_letter'
    if not x[0].text.strip():
        log.error('species has no name')
        return None  # signal an empty species block
    assert x[1].tag == 'bold_italic'
    name = x[1].text.strip()

    # Paste genus and species names that get stranded in separate elements.
    if (' ' not in name and x[2].tag == 'bold_italic'):
        name += ' ' + x[2].text.strip()

    return norm(name)


def trailing_taxon_name(prefix, x):
    n = -1
    while not x[n].text.strip():
        n -= 1
    xe = x[n]
    name = norm(xe.text.strip())
    if len(name) and name[1:2] == '.':  # like "H. appressa"
        name = name[2:].strip()
    if prefix:
        name = prefix + ' ' + name
    name = norm(name)
    log.info('       -> %s', name)
    return name

def parse_section(info, page, prefix, xchildren, i):
    lead_stack = [ None ]

    log.info('    start of section')

    if i < len(xchildren) and xchildren[i].tag == 'text_indent_02':
        # TODO: have this snarf in the paragraphs to make the genus page
        # bugger
        #
        # species_name = xchildren[i][0].text.strip()
        # parent.add_lead(Lead(result=Couplet.get(species_name)))
        return i + 1

    while i < len(xchildren):

        fix_typo1(xchildren, i)
        fix_empty_italic(xchildren, i)
        fix_typo2(xchildren, i)
        fix_typo4(xchildren, i)

        xchild = xchildren[i]

        if is_empty(xchild):  # ignore empty elements
            log.warn('empty <%s>', xchild.tag)
            i += 1
            continue

        if not is_lead(xchild):
            log.info('    end of section; <%s> is next', xchild.tag)
            break

        digits = ''.join( c for c in xchild[0].text if c.isdigit() )
        newlen = int(digits)
        if newlen < len(lead_stack):
            del lead_stack[newlen:]
        elif newlen > len(lead_stack):
            lead_stack.extend([ lead_stack[-1] ] * (newlen - len(lead_stack)))

        assert len(lead_stack) == newlen, (len(lead_stack), newlen)

        lead = info.create_lead(page, parent=lead_stack[-1])
        lead.letter = xchild[0].text.strip().strip('.')  # like '1a'
        lead_stack.append(lead)

        log.info('     %s <%s>', lead.letter, xchild.tag)
        endskip = 0

        x = xchild.find('trailing_group_designation')
        if x is not None:
            group_name = x.text.strip()
            if page.rank == 'family' or page.rank == 'genus':
                # 'Group 1' -> 'Asteraceae Group 1'
                group_name = page.title + ' ' + group_name
            lead.goto_page = info.get_or_create_page(group_name)

        x = xchild.find('trailing_genus_designation')
        if x is not None:
            taxon_name = x.text.strip()
            if taxon_name.startswith('go to couplet '):
                lead.goto_num = int(taxon_name.split()[-1])
            else:
                lead.goto_page = info.get_or_create_page(taxon_name)

        if not (xchild[-1].text or '').strip() and xchild[-1].tag in (
            'italic', 'lead_number_letter', 'lead_number_letter_inner',
            ):
            del xchild[-1]  # 'I. hieroglyphica' has a stray empty <italic>

        if xchild[-1].tag == 'bold_italic' and xchild[-1].text.strip():
            taxon_name = trailing_taxon_name(prefix, xchild)
            lead.goto_page = info.get_or_create_page(taxon_name)
            endskip = 1

        lead.text += extract_html(xchild, skip=1, endskip=endskip)

        i += 1

    return i

# Special cases that will hopefully get cleaned up.

def fix_typo1(xchildren, i):
    if len(xchildren) < i + 2:
        return
    ci = xchildren[i]
    cj = xchildren[i+1]
    if (ci.tag == cj.tag == 'text_indent_08'
        and cj.text.strip() == '(in part)'):
        log.error('fixing special typo #1')
        ci[0].tail += cj.text
        while len(cj):
            ci.append(cj[0])
        del xchildren[i+1]

def fix_empty_italic(xchildren, i):
    x = xchildren[i]
    if len(x) and x[-1].tag == 'italic' and not (x[-1].text or '').strip():
        del x[-1]

def fix_typo2(xchildren, i):
    x = xchildren[i]
    if (x.tag.startswith('text_indent') and len(x) > 1
        and (x[-2].tag == 'bold_ex' or x[-1].tag == 'bold_ex')):
        log.error('repairing split "ex"')
        doomed = -1 if x[-1].tag == 'bold_ex' else -2
        fulltext = x[-2].text + x[-1].text
        del x[doomed]
        x[-1].text = fulltext
        while len(x) > 2 and x[-2].tag == 'bold_italic':
            x[-1].text = x[-2].text + x[-1].text
            del x[-2]

def fix_typo3(xchildren, i):
    x = xchildren[i]
    if (len(x) > 3 and x[1].text == 'Fraxinus' and x[2].text == 'ex'
        and x[3].text == 'celsior'):
        del x[3]
        del x[2]
        x[1].text = 'Fraxinus excelsior'

def fix_typo4(xchildren, i):
    if i < 4 or len(xchildren[i]) == 0 or len(xchildren[i-3]) == 0:
        return
    if ((xchildren[i][0].text or '').strip() !=
        (xchildren[i-3][0].text or '').strip()):
        return
    log.error('repairing duplicate "%s"' % xchildren[i][0].text.strip())
    xchildren[i][0].text = xchildren[i][0].text.replace('a', 'b')

# Support command-line invocation.

def do_parse(filename):
    # Start with empty dkey tables (this is safe, because we are inside
    # of a transaction, and because the rest of the database holds no
    # foreign keys to dkey tables; instead, family, genus, and species
    # names are looked up literally when relating normal database
    # objects to the dkey).

    cursor = connection.cursor()
    cursor.execute('DELETE FROM dkey_figure')
    cursor.execute('DELETE FROM dkey_lead')
    cursor.execute('DELETE FROM dkey_page_breadcrumb_cache')
    cursor.execute('DELETE FROM dkey_page')

    # The actual parsing.

    info = parse(filename)

    # Save the changes that have been made to pages and leads since
    # their initial creation.

    for page in info.pages.values():
        page.save()
    for lead in info.leads:
        lead.save()

    # Save figure captions.

    for n, caption in sorted(info.captions.items()):
        f = models.Figure()
        f.number = n
        f.caption = caption
        f.save()

if __name__ == '__main__':
    import argparse
    import logging

    logging.basicConfig(filename='log.dkey', level=logging.DEBUG)
    logging.getLogger('django').level = logging.INFO

    parser = argparse.ArgumentParser(
        description='Import the Flora Nova Angliae XML into the database',
        )
    parser.add_argument('filename', help='name of the file to load',
                        nargs='?', default='110330_fone_test_05.xml')
    args = parser.parse_args()

    transaction.commit_on_success(do_parse)(args.filename)
