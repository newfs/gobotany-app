# Dichotomous Key

## Updating the Dichotomous Key

To make changes to the Dichotomous Key in order to keep it up to date,
edit the records in the Admin. Then a site administrator should run
the `sync` script, which will complete the update.

Here are various pieces of the Dichotomous Key and how to update them:

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