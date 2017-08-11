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

### Adding new leads

In adding a new lead to the key, you essentially need to split an existing
lead in two. This is because, with the key being a dichotomous key, all
choices are arranged in couplets. Each couplet consists of two mutually
exclusive choices for the user, and each of these choices is really a lead.
So, you're really adding a pair of leads.

1. Find the Page

Start by finding the page that you will need to add a new lead on. This
can be the top page (“Key to the Families”), a group page (ex.: ”Group 3”),
a family page, or a genus page. Each of those can have a structure of
leads.

Browse around the [Compact View](/edit/dkey/) tool to get the page where
you will need to add your new lead. You can click the `change` link at top
to see the database record for this page, although you will likely not need
to change it.

For example, choose the Group 4 page.

2. Find the Parent Lead

The next step is to find the parent lead that you want your new leads to
appear beneath. Jot down the ID of this parent as seen in the Compact
View tool.

For example, on the Group 4 page, choose 179:2a (which has 7 families)
as your Parent Lead.

3. Note the existing Child Leads

The next step is to jot down the IDs of the existing child leads. This is the
couplet of two choices underneath your Parent Lead.

So, for example, under Group 4's 179:2a, the two child leads are 180:3a.74
(which points to the Staphyleaceae page) and 181:3b (which has 6 families).

[3.5: decide on "letters" for the child leads; shouldn't these usually be
numbered just beneath the parent numbers? ex., parent is 2a, children will
be 3a and 3b?]

4. Create two records for your new Leads

In the CMS, go create the two new records for your new leads, and write
down the IDs of them.

Set the Page to the one you noted earlier.

Set the Parent field to the Parent Lead ID you jotted down. You can type in
order to make the browser find the value in the long list more quickly.

Set the Letter field to whatever you decided earlier, one for each record.

Set the text to whatever the description in the user interface should be.

If appropriate, set the Goto Page field to a destination Page record. This
will only be set if your lead goes to another page, rather than is just a
lead for narrowing down results on the same page.

The field Goto Num can be left blank for now, as can Taxa Cache.

(after I do this, I get the error Lead object has no attribute childlist)

5. Get the two new IDs of the two lead records you just created. You can
do a search on the field above the table in the CMS to narrow down the
results.

For my example, after creating two new leads with "letters" 3a and 3b,
with 179:2a as the parent, I ended up with new records of ID 8745 and
8746, respectively.

5. Change the old child leads to point to one of the new leads as its
parent ID.

So, in this case, I'll choose my new 3a as the lead which will connect
the old child leads (180:3a.74 and 181:3b).

Combine the ID for this lead with its "letter" and you get the full ID of
this lead. So, 8745.3a.

Go to the old child leads (search on the ID number in the CMS's search
field), and set the Parent to this, 8745.3a.

For now, check your Parent ID in the Compact View: you should see your
new leads, with the old child leads now connected under one of them.

The second new child lead will have to go either to another page, or to
other leads; that's for the next step.

Also, note that if you are connecting a sub-structure of old child leads
under your new one, that you may need to go through and re-number the
Letter field for all the leads beneath your new one. So, if you inserted
a new 3a lead, you will likely want to re-number everything below it to
follow in numerical order, i.e., 4a, 4b, 5a, 5b, 6a, 6b, etc.

6. For the second new lead, make it go somewhere.

Your second new lead, 8746.3b, is hanging out there with nowhere to go.
Go back to the CMS and search on 8746 to find that record. Edit it, and
you can choose a Page record for it to point to (e.g., a family page or
a genus page).

If you would rather instead add more leads beneath this one, you can go
create two new Leads records (see step 4), and set their Parent to this
lead.

Again, go test in the Compact View to see the results of your changes.

Then you can, of course, go try out your changes in the actual D. Key
as well.


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