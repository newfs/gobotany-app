# Dichotomous Key

## Updating the Dichotomous Key

To update the key, edit the records in the Admin (CMS) as described in the
following instructions.

Periodically, a site administrator should run the `sync` script, which will
finish the update by rebuilding the ”caches” of taxa.

### D. Key Editor

The D. Key Editor is a companion to the regular CMS screens. You can access
it from a link in the top right of the ”Dichotomous Key Administration” page.

This allows you to browse a compact, expanded view of the key. You can
navigate using the links at top, and the links to groups, families,
and genera in the trees. Generally, links are for navigating and buttons are
for making changes.

Each page in the D. Key Editor corresponds to a page in the key. The page
title appears at the top, with a Change button next to it for editing the
record for that page.

Each lead has its number and letter, followed by a text excerpt, a
Change button, possibly either an Add Couplet or Delete Couplet button,
and the number of families (or genera, or species).

If the lead goes to a group, family, or genus, a link is displayed that goes
to the corresponding page in the D. Key Editor.

If you hover your cursor over a lead’s number-and-letter or text excerpt,
the full text for that couplet question will appear as a tooltip.

### Changing leads

You can edit a lead at any time by pressing its Change button in teh
D. Key Editor.

This will take you to the Change page for that lead record, where you
can edit various fields for that lead.

### Adding new leads

You can add a new couplet, consisting of two leads, by pressing an
Add Couplet button on a lead that does not yet have a couplet in the
D. Key Editor.

Upon adding a couplet, you will see the A and B questions of the couplet
have been added in place, and the key renumbered.

Remember to edit the text of the A and B questions, along with all
the fields of those new records, especially the destination of those
couplets.

Finally, go back and edit the parent of that couplet. If it pointed to
another part of the key before (such as a family page), normally you
will want to remove that. One of the new couplet's leads may now be
pointing there instead.

### Deleting leads

You can delete a couplet, consisting of two leads, by pressing a
Delete Couplet button in the D. Key Editor.

Upon deleting a couplet, the key will be renumbered.

Note that not every couplet can be immediately deleted: only ones
at the bottom-most branches of a page's tree. So, there is no way
to delete couplets which have further child couplets, without deleting
starting from the bottom first.

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