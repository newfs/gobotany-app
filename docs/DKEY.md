# Dichotomous Key

## Updating the Dichotomous Key

To update the key, edit the records in the Admin (CMS) as described in the
following instructions. Then a site administrator should run the `sync`
script, which will finish the update.

### Compact View Tool

The Compact View tool is a companion to the CMS screens. You can access it
from a link in the top right of the ”Dichotomous Key Administration” page.

This allows you to browse a compact, expanded view of the key. This makes
it easier to see what is where and to provide quick shortcuts to the edit
screens. Navigate using the links at top, and the links to groups, families,
and genera in the trees.

Each page in the Compact View corresponds to a page in the key. The page
title appears at the top, with a `change` link next to it for editing the
record for that page.

Each lead has its number and letter, followed by its composite identifier
(page id:lead-number-and-letter, which looks like this: 16:8b), a
`change` link, and the number of families (or genera, or species).

If the lead goes to a group, family, or genus, a link is displayed that goes
to the corresponding page in the Compact View.

If you hover your cursor over a lead’s number-and-letter or identifier, the
text for that couplet question will appear as a tooltip.

### Adding new leads

In adding a new lead to the key, you essentially need to split an existing
lead in two. This is because all choices are arranged in couplets, each
consisting of two mutually exclusive choices. Each of these choices is
a lead. So, you are really adding a pair of leads.

#### 1. Find the Page

Start by finding the page that you will need to add new leads on. This
can be the top page (“Key to the Families”), a group page (ex.: ”Group 3”),
a family page, or a genus page. Each of those can have a structure of
leads.

Browse around the Compact View tool to get the page where you will need to
add your new leads. You can click the `change` link at top to see the record
for this page, although you will likely not need to change it.

For example, choose the Group 4 page.

#### 2. Find the Parent Lead

The next step is to find the parent lead that you want your new leads to
appear beneath. Jot down the ID of this parent as seen in the Compact
View tool.

For example, on the Group 4 page, choose 179:2a (which has 7 families)
as your Parent Lead.

#### 3. Note the existing Child Leads

The next step is to jot down the IDs of the existing child leads. This is the
couplet of two choices underneath your Parent Lead.

So, for example, under Group 4’s 179:2a, the two child leads are 180:3a.74
(which points to the Staphyleaceae page) and 181:3b (which has 6 families).

You will need to decide on the number-letter IDs for the new child leads.
Normally these are ordered just beneath the parent numbers. For example, if
the parent is 2a, child leads would be 3a and 3b. Numbers are not reused
within a single page. So, on your page in the Dichotomous Key, press the
Show All Couplets button to the full hierarchy of leads and number-letter
identifiers.

If your leads come in the middle of a page, it would be best to plan to
re-number the rest of the leads on the page, in order to maintain the
top-to-bottom sequence, i.e., 1a, 1b, 2a, 2b, etc. You can do this later
if you like.

#### 4. Create two records for your new Leads

In the CMS, go create the two new records for your new leads, and write
down the IDs of them.

Set the value of Page field to the one you noted earlier.

Set the Parent field to the Parent Lead ID you jotted down. You can type in
order to make the browser find the value in the long list more quickly.

Set the Letter field to whatever you decided earlier, one for each record.

Set the text to whatever the description in the user interface should be.

If appropriate, set the Goto Page field to a destination Page record. This
will only be set if your lead goes to another page, rather than is just a
lead for narrowing down results on the same page.

The field Goto Num can be left blank for now, as can Taxa Cache.

(TODO: investigate: after doing this, got an error: Lead object has no
attribute childlist)

#### 5. Get the two new IDs of the two lead records you just created. You
can do a search on the field above the table in the CMS to narrow down the
results.

For my example, after creating two new leads with “letters” 3a and 3b,
with 179:2a as the parent, I ended up with new records of ID 8745 and
8746, respectively.

#### 6. Change the old child leads to point to one of the new leads as its
parent ID.

So, in this case, I will choose my new 3a as the lead which will connect
the old child leads (180:3a.74 and 181:3b).

Combine the ID for this lead with its “letter” and you get the full ID of
this lead. So, 8745.3a.

Go to the old child leads (search on the ID number in the CMS’s search
field), and set the Parent to this, 8745.3a.

For now, check your Parent ID in the Compact View: you should see your
new leads, with the old child leads now connected under one of them.

The second new child lead will have to go either to another page, or to
other leads; that is for the next step.

Also, note that if you are connecting a sub-structure of old child leads
under your new one, that you may need to go through and re-number the
Letter field for all the leads beneath your new one. So, if you inserted
a new 3a lead, you will likely want to re-number everything below it to
follow in numerical order, i.e., 4a, 4b, 5a, 5b, 6a, 6b, etc. As mentioned
before, you can wait until a bit later to do this.

#### 7. For the second new lead, make it go somewhere.

Your second new lead, 8746.3b, is hanging out there with nowhere to go.
Go back to the CMS and search on 8746 to find that record. Edit it, and
you can choose a Page record for it to point to (e.g., a family page or
a genus page).

If you would rather instead add more leads beneath this one, you can go
create two new Leads records (see step 4), and set their Parent to this
lead.

Again, you can test in the Compact View to see the results of your changes,
and then try them in the actual D. Key too.

#### 8. Re-number any leads that come after the new ones on the page.

As mentioned in earlier steps above, you can now re-number all the leads
that come after the ones you just added to your page. This way each lead
on the page will have a unique letter-number identifier, and the ascending
sequence of these identifiers will be maintained.

[TODO: investigate if there are any special problems or tricks for doing
this renaming: is it extra difficult? Does it have to be done a certain way?]

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