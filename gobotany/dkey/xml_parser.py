# -*- coding: utf-8 -*-

import logging
import re
from lxml import etree
from dkey.model import Couplet, couplet_entitled, couplet_make

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
         .replace(u'–', u'–\u2060')    # tell n-dashes not to break
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

class Info(object):
    """Information that we gleaned from reading Flora Novae Angliae."""

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
        parse_chapter(xchapter)

    # Find the figure captions.

    info.captions = {}
    xcaptions = root.find('.//caption_list').findall('caption')
    for i, xcaption in enumerate(xcaptions):
        n = i + 1
        assert xcaption[0].text == u'Fig.\u2009%03d\u2002' % n
        info.captions[n] = extract_html(xcaption, skip=1)

    # Find families and genera.

    couplets = Couplet.all_couplets
    info.families = sorted(c.title for c in couplets if c.rank == 'family')
    info.genera = sorted(c.title for c in couplets if c.rank == 'genus')

    # All done.

    return info

# The big chapter parser.

def parse_chapter(xchapter):
    most_recent_taxon = None  # used to label Groups more specifically
    genus_name = None  # used to expand abbreviated genus names
    species_comes_next = False  # when we know it's a species, darn it
    children = list(xchapter)
    xtitle = children[0]
    assert xtitle.tag == 'chapter_title', repr(xtitle.tag)
    title = xtitle.text.strip()
    log.info('* %s', title)

    # The initial Key to the Families chapter starts right off with a
    # series of couplets; subsequent chapters have headings instead, so
    # we can skip on down to the section-processing logic below.

    if title == u'Key to the Families':
        couplet = couplet_make(title)
        i = parse_section(None, couplet, children, 1)
    else:
        i = 1

    # As long as there are sections remaining, process them.

    while i < len(children):
        child = children[i]
        tag = child.tag

        if species_comes_next or is_species(child):

            # It's a species!

            fix_typo3(children, i)

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
            couplet = couplet_entitled(name)
            couplet.rank = 'species'
            couplet.texts.append(extract_html(child, skip=0))
            i += 1
            while i < len(children) and (is_discourse(children[i])
                or is_lead(children[i]) and not is_species(children[i])):
                # (children[i].tag in (
                # 'text_no_indent_description',
                # 'text_no_indent_no_leader',
                # ) or children[i].tag in level_tags  #ack! really?
                #):
                log.info('    species descriptive <%s>', children[i].tag)
                couplet.texts.append(extract_html(children[i]))
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

        couplet = couplet_entitled(heading)
        couplet.rank = rank
        couplet.chapter = title
        i += 1

        # Special case a genus with only one species. (Epimedium)

        if rank == 'genus' and children[i].tag == 'text_indent_02':
            name = children[i][0].text.strip()
            couplet.new_lead().set_result(Couplet(name))
            # we do NOT advance `i` so the species will be processed next
            species_comes_next = True
            continue

        # Then we grab the following paragraphs as part of this
        # couplet's description.

        while is_discourse(children[i]):
            log.info('    descriptive <%s>', children[i].tag)
            couplet.texts.append(extract_html(children[i]))
            i += 1

        # Special case another style of genus with only one species.

        if rank == 'genus' and genus_name in ('Convolvulus', 'Rhodotypos'):
            name = children[i].find('bold_italic').text.strip()
            couplet.new_lead().set_result(Couplet(name))
            # we do NOT advance `i` so the species will be processed next
            species_comes_next = True
            continue

        # Assume that we must be looking at a heading.

        if i >= len(children):
            pass
        elif children[i].tag in level_tags:
            i = parse_section(prefix, couplet, children, i)
        elif couplet.rank == 'family' and children[i].tag == 'head_2':
            # the family has only one genus
            next_heading = children[i].text.strip()
            couplet.new_lead().set_result(Couplet(next_heading))
            # we do NOT advance `i` so the heading will be processed next
        elif couplet.rank in ('tribe', 'subgroup') \
                and re_1_species.search(children[i].text):
            name = trailing_taxon_name(genus_name, children[i])
            couplet.new_lead().set_result(Couplet(name))
            i += 1
        elif couplet.rank == 'genus' and children[i].tag == \
                'text_no_indent_no_leader':
            name = leading_species_name(children[i])
            couplet.new_lead().set_result(Couplet(name))
            # we do NOT advance `i` so the species will be processed next

        elif children[i].tag == 'head_4':
            # alternate keys, like 'Key for carpellate reproductive material'
            while i < len(children) and children[i].tag == 'head_4':
                title = ' '.join((most_recent_taxon,
                                  children[i].text.strip().lower()))
                log.info(' ** %s', title)
                c2 = Couplet(title)
                c2.rank = 'subkey'
                couplet.new_lead().set_result(c2)
                i = parse_section(prefix, c2, children, i + 1)
        else:
            log.error('not sure what to do with <%s>' % children[i].tag)


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

def parse_section(prefix, parent, children, i):
    couplet_stack = [ parent ]

    log.info('    start of section')

    if i < len(children) and children[i].tag == 'text_indent_02':
        # TODO: have this snarf in the paragraphs to make the genus page
        # bugger
        #
        # species_name = children[i][0].text.strip()
        # parent.add_lead(Lead(result=Couplet.get(species_name)))
        return i + 1

    while i < len(children):

        fix_typo1(children, i)
        fix_empty_italic(children, i)
        fix_typo2(children, i)
        fix_typo4(children, i)

        xchild = children[i]

        if is_empty(xchild):  # ignore empty elements
            log.warn('empty <%s>', xchild.tag)
            i += 1
            continue

        if not is_lead(xchild):
            log.info('    end of section; <%s> is next', xchild.tag)
            break

        digits = ''.join( c for c in xchild[0].text if c.isdigit() )
        newlen = int(digits)
        if newlen < len(couplet_stack):
            del couplet_stack[newlen:]
        elif newlen > len(couplet_stack):
            if newlen > len(couplet_stack) + 1:
                # log.warn('<%s> immediately followed by <%s>',
                #          children[i-1].tag, children[i].tag)
                while newlen > len(couplet_stack) + 1:
                    # fake a correct stack by duplicating the top stack entry
                    couplet_stack.append(couplet_stack[-1])
            couplet_stack.append(Couplet())
            couplet_stack[-2].leads[-1].set_result(couplet_stack[-1])

        assert len(couplet_stack) == newlen, (len(couplet_stack), newlen)

        lead = couplet_stack[-1].new_lead()
        lead.letter = xchild[0].text.strip()  # like '1a.'
        log.info('     %s <%s>', lead.letter, xchild.tag)
        endskip = 0

        x = xchild.find('trailing_group_designation')
        if x is not None:
            group_name = x.text.strip()
            if parent.rank == 'family' or parent.rank == 'genus':
                # 'Group 1' -> 'Asteraceae Group 1'
                group_name = parent.title + ' ' + group_name
            lead.set_result(couplet_make(group_name))

        x = xchild.find('trailing_genus_designation')
        if x is not None:
            taxon_name = x.text.strip()
            lead.set_result(couplet_make(taxon_name))

        if not (xchild[-1].text or '').strip() and xchild[-1].tag in (
            'italic', 'lead_number_letter', 'lead_number_letter_inner',
            ):
            del xchild[-1]  # 'I. hieroglyphica' has a stray empty <italic>

        if xchild[-1].tag == 'bold_italic' and xchild[-1].text.strip():
            taxon_name = trailing_taxon_name(prefix, xchild)
            lead.set_result(couplet_make(taxon_name))
            endskip = 1

        lead.text = extract_html(xchild, skip=1, endskip=endskip)

        i += 1

    return i

# Special cases that will hopefully get cleaned up.

def fix_typo1(children, i):
    if len(children) < i + 2:
        return
    ci = children[i]
    cj = children[i+1]
    if (ci.tag == cj.tag == 'text_indent_08'
        and cj.text.strip() == '(in part)'):
        log.error('fixing special typo #1')
        ci[0].tail += cj.text
        while len(cj):
            ci.append(cj[0])
        del children[i+1]

def fix_empty_italic(children, i):
    x = children[i]
    if len(x) and x[-1].tag == 'italic' and not (x[-1].text or '').strip():
        del x[-1]

def fix_typo2(children, i):
    x = children[i]
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

def fix_typo3(children, i):
    x = children[i]
    if (len(x) > 3 and x[1].text == 'Fraxinus' and x[2].text == 'ex'
        and x[3].text == 'celsior'):
        del x[3]
        del x[2]
        x[1].text = 'Fraxinus excelsior'

def fix_typo4(children, i):
    if i < 4 or len(children[i]) == 0 or len(children[i-3]) == 0:
        return
    if ((children[i][0].text or '').strip() !=
        (children[i-3][0].text or '').strip()):
        return
    log.error('repairing duplicate "%s"' % children[i][0].text.strip())
    children[i][0].text = children[i][0].text.replace('a', 'b')
