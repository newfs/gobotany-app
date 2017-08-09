# Dichotomous Key

## Updating the Dichotomous Key

To make changes to the Dichotomous Key in order to keep it up to date,
edit the records in the Admin. Then a site administrator should run
the `sync` script, which will complete the update.

Below are various pieces of the Dichotomous Key and how to update them.

### Compact View Tool

The [Compact View](/edit/dkey/) tool is a companion to the CMS screens.

It enables you to browse a compact, expanded view of the key. It aims to
make it easier to see what is where and to provide quick shortcuts to the
CMS edit screens. Navigate using the links at top, and the links to groups,
families, and genera in the trees.

Each page in the Compact View corresponds to a page in the key. Its title
appears at the top of the page, with a `change` link next to it in case
you need to edit that page record.

Each lead has its composite identifier (page id:lead number/letter, which
looks like this: 16:8b) linked to the CMS change screen for that record.
If there's a group, family, or genus link next to it, that link goes to
another page in the Compact View.

If you hover your cursor over a lead’s identifier in the Compact View for
a couple of seconds, the text for that couplet question will appear as a
tooltip.

### Text at bottom of species pages

Each species page on the site has a section labeled *Information from
Dichotomous Key of Flora Novae Angliae.*

To update this section, go to the Dichotomous Key pages screen in the
Admin and find the desired plant by species name. Then edit the record,
updating the HTML in the field named `Text`.

### Text within a couplet question

Go to Leads. In the search box, search on some text from that question
that is likely to be unique or uncommon. Upon finding the correct
record, edit it.

### Steps for changing the name of a plant

In addition to the other areas in the Admin that need to be edited when
renaming a plant, here are the things to change in the Dichotomous Key
records. The following items each pertain to a section in the Home >
Dichotomous Key section of the Admin:

1. **Dichotomous Key Pages:** use the search box to search on the
genus. You should get a list of all the species records plus a genus
page record. Edit the species page record. If necessary, edit the
genus page record.
2. **Figures:** use the search box to search on the genus. If there
are any relevant records for the plant, edit as necessary.
3. **Hybrids:** use the search box to search on the genus. If there
are any relevant records for the plant, edit as necessary.
4. **Illustrative Species:** use the search box to see whether the
plant being changed is present in these records. If so, edit as
necessary.
5. **Leads:** use the search box to see whether the plant being
changed is present in these records. If so, edit as necessary.

### Lists of families, genera, species

Throughout the key, there are lists of families, genera, and species.
These are also presented as a set of thumbnail images at the bottom
of the pages. The contents of these lists are constructed from the
current data set by the views code of the application. The lists are
not directly editable in the Admin. However, one should be able to
update them indirectly by changing or adding the appropriate records
in the Admin for the Dichotomous Key.

In order for these lists to be correct and up to date on the site, the
sync script must be run, which updates the breadcrumb and taxa
caches. The taxa caches in particular are used to help populate the
lists for the pages.

### Running the sync script

After each batch of changes to the key, a site administrator should run
the `sync` script. This rebuilds the contents of some cache fields for
the key. It takes just a few minutes to run.

The command on Heroku:

    heroku run python gobotany/dkey/sync.py --app {app-name}

The command for local development:

    python gobotany/dkey/sync.py