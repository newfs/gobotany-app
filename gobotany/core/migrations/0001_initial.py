# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Parameter'
        db.create_table(u'core_parameter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('value', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal(u'core', ['Parameter'])

        # Adding model 'CharacterGroup'
        db.create_table(u'core_charactergroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
        ))
        db.send_create_signal(u'core', ['CharacterGroup'])

        # Adding model 'GlossaryTerm'
        db.create_table(u'core_glossaryterm', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('term', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('lay_definition', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('highlight', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['GlossaryTerm'])

        # Adding unique constraint on 'GlossaryTerm', fields ['term', 'lay_definition']
        db.create_unique(u'core_glossaryterm', ['term', 'lay_definition'])

        # Adding model 'Character'
        db.create_table(u'core_character', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('short_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('friendly_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('character_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.CharacterGroup'])),
            ('pile', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='characters', null=True, to=orm['core.Pile'])),
            ('ease_of_observability', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('value_type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('question', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('hint', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['Character'])

        # Adding model 'CharacterValue'
        db.create_table(u'core_charactervalue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value_str', self.gf('django.db.models.fields.CharField')(max_length=260, null=True, blank=True)),
            ('value_min', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('value_max', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('value_flt', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('character', self.gf('django.db.models.fields.related.ForeignKey')(related_name='character_values', to=orm['core.Character'])),
            ('friendly_text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['CharacterValue'])

        # Adding model 'Pile'
        db.create_table(u'core_pile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
            ('friendly_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('friendly_title', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Video'], null=True)),
            ('key_characteristics', self.gf('tinymce.models.HTMLField')(blank=True)),
            ('notable_exceptions', self.gf('tinymce.models.HTMLField')(blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('pilegroup', self.gf('django.db.models.fields.related.ForeignKey')(related_name='piles', null=True, to=orm['core.PileGroup'])),
        ))
        db.send_create_signal(u'core', ['Pile'])

        # Adding M2M table for field species on 'Pile'
        db.create_table(u'core_pile_species', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pile', models.ForeignKey(orm[u'core.pile'], null=False)),
            ('taxon', models.ForeignKey(orm[u'core.taxon'], null=False))
        ))
        db.create_unique(u'core_pile_species', ['pile_id', 'taxon_id'])

        # Adding model 'PileImage'
        db.create_table(u'core_pileimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ContentImage'])),
            ('pile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Pile'])),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'core', ['PileImage'])

        # Adding model 'PileGroup'
        db.create_table(u'core_pilegroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=100)),
            ('friendly_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('friendly_title', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Video'], null=True)),
            ('key_characteristics', self.gf('tinymce.models.HTMLField')(blank=True)),
            ('notable_exceptions', self.gf('tinymce.models.HTMLField')(blank=True)),
        ))
        db.send_create_signal(u'core', ['PileGroup'])

        # Adding model 'PileGroupImage'
        db.create_table(u'core_pilegroupimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content_image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ContentImage'])),
            ('pile_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.PileGroup'])),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'core', ['PileGroupImage'])

        # Adding model 'ImageType'
        db.create_table(u'core_imagetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=4)),
        ))
        db.send_create_signal(u'core', ['ImageType'])

        # Adding model 'ContentImage'
        db.create_table(u'core_contentimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=300)),
            ('alt', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('rank', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('creator', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('image_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ImageType'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'core', ['ContentImage'])

        # Adding model 'HomePageImage'
        db.create_table(u'core_homepageimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('partner_site', self.gf('django.db.models.fields.related.ForeignKey')(related_name='home_page_images', to=orm['core.PartnerSite'])),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
        ))
        db.send_create_signal(u'core', ['HomePageImage'])

        # Adding model 'Family'
        db.create_table(u'core_family', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('common_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'core', ['Family'])

        # Adding model 'Genus'
        db.create_table(u'core_genus', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('common_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('family', self.gf('django.db.models.fields.related.ForeignKey')(related_name='genera', to=orm['core.Family'])),
        ))
        db.send_create_signal(u'core', ['Genus'])

        # Adding model 'Synonym'
        db.create_table(u'core_synonym', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scientific_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('taxon', self.gf('django.db.models.fields.related.ForeignKey')(related_name='synonyms', to=orm['core.Taxon'])),
        ))
        db.send_create_signal(u'core', ['Synonym'])

        # Adding model 'CommonName'
        db.create_table(u'core_commonname', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('common_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('taxon', self.gf('django.db.models.fields.related.ForeignKey')(related_name='common_names', to=orm['core.Taxon'])),
        ))
        db.send_create_signal(u'core', ['CommonName'])

        # Adding model 'Lookalike'
        db.create_table(u'core_lookalike', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lookalike_scientific_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('lookalike_characteristic', self.gf('django.db.models.fields.CharField')(max_length=900, blank=True)),
            ('taxon', self.gf('django.db.models.fields.related.ForeignKey')(related_name='lookalikes', to=orm['core.Taxon'])),
        ))
        db.send_create_signal(u'core', ['Lookalike'])

        # Adding model 'WetlandIndicator'
        db.create_table(u'core_wetlandindicator', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=15)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('friendly_description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('sequence', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'core', ['WetlandIndicator'])

        # Adding model 'Taxon'
        db.create_table(u'core_taxon', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scientific_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('family', self.gf('django.db.models.fields.related.ForeignKey')(related_name='taxa', to=orm['core.Family'])),
            ('genus', self.gf('django.db.models.fields.related.ForeignKey')(related_name='taxa', to=orm['core.Genus'])),
            ('taxonomic_authority', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('factoid', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('wetland_indicator_code', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('north_american_native', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('north_american_introduced', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('variety_notes', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
        ))
        db.send_create_signal(u'core', ['Taxon'])

        # NOTE: This is commented out because it's redundant.  We have an odd
        # scenario where we've manually chosen the SAME M2M table for two
        # different relationships, which fools South's auto-detection.
        #
        # Adding M2M table for field piles on 'Taxon'
        #db.create_table(u'core_pile_species', (
        #    ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
        #    ('taxon', models.ForeignKey(orm[u'core.taxon'], null=False)),
        #    ('pile', models.ForeignKey(orm[u'core.pile'], null=False))
        #))
        #db.create_unique(u'core_pile_species', ['taxon_id', 'pile_id'])

        # Adding model 'SourceCitation'
        db.create_table(u'core_sourcecitation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('citation_text', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('publication_year', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('article_title', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('publication_title', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('publisher_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('publisher_location', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal(u'core', ['SourceCitation'])

        # Adding model 'TaxonCharacterValue'
        db.create_table(u'core_taxoncharactervalue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('taxon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Taxon'])),
            ('character_value', self.gf('django.db.models.fields.related.ForeignKey')(related_name='taxon_character_values', to=orm['core.CharacterValue'])),
            ('literary_source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='taxon_character_values', null=True, to=orm['core.SourceCitation'])),
        ))
        db.send_create_signal(u'core', ['TaxonCharacterValue'])

        # Adding unique constraint on 'TaxonCharacterValue', fields ['taxon', 'character_value']
        db.create_unique(u'core_taxoncharactervalue', ['taxon_id', 'character_value_id'])

        # Adding model 'Edit'
        db.create_table(u'core_edit', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('author', self.gf('django.db.models.fields.TextField')()),
            ('datetime', self.gf('django.db.models.fields.DateTimeField')()),
            ('itemtype', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('coordinate1', self.gf('django.db.models.fields.TextField')()),
            ('coordinate2', self.gf('django.db.models.fields.TextField')()),
            ('old_value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'core', ['Edit'])

        # Adding model 'ConservationLabel'
        db.create_table(u'core_conservationlabel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('taxon', self.gf('django.db.models.fields.related.ForeignKey')(related_name='conservation_labels', to=orm['core.Taxon'])),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=80)),
        ))
        db.send_create_signal(u'core', ['ConservationLabel'])

        # Adding unique constraint on 'ConservationLabel', fields ['taxon', 'region', 'label']
        db.create_unique(u'core_conservationlabel', ['taxon_id', 'region', 'label'])

        # Adding model 'ConservationStatus'
        db.create_table(u'core_conservationstatus', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('taxon', self.gf('django.db.models.fields.related.ForeignKey')(related_name='conservation_statuses', to=orm['core.Taxon'])),
            ('variety_subspecies_hybrid', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('s_rank', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('endangerment_code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('allow_public_posting', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'core', ['ConservationStatus'])

        # Adding model 'DefaultFilter'
        db.create_table(u'core_defaultfilter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('pile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Pile'])),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('character', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Character'], null=True)),
        ))
        db.send_create_signal(u'core', ['DefaultFilter'])

        # Adding unique constraint on 'DefaultFilter', fields ['key', 'pile', 'character']
        db.create_unique(u'core_defaultfilter', ['key', 'pile_id', 'character_id'])

        # Adding model 'PartnerSite'
        db.create_table(u'core_partnersite', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('short_name', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal(u'core', ['PartnerSite'])

        # Adding M2M table for field users on 'PartnerSite'
        db.create_table(u'core_partnersite_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('partnersite', models.ForeignKey(orm[u'core.partnersite'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'core_partnersite_users', ['partnersite_id', 'user_id'])

        # Adding model 'PartnerSpecies'
        db.create_table(u'core_partnerspecies', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('species', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Taxon'])),
            ('partner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.PartnerSite'])),
            ('simple_key', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('species_page_heading', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('species_page_blurb', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'core', ['PartnerSpecies'])

        # Adding unique constraint on 'PartnerSpecies', fields ['species', 'partner']
        db.create_unique(u'core_partnerspecies', ['species_id', 'partner_id'])

        # Adding model 'PlantPreviewCharacter'
        db.create_table(u'core_plantpreviewcharacter', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Pile'])),
            ('character', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Character'])),
            ('partner_site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.PartnerSite'], null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'core', ['PlantPreviewCharacter'])

        # Adding unique constraint on 'PlantPreviewCharacter', fields ['pile', 'character', 'partner_site']
        db.create_unique(u'core_plantpreviewcharacter', ['pile_id', 'character_id', 'partner_site_id'])

        # Adding model 'Distribution'
        db.create_table(u'core_distribution', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scientific_name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('county', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('present', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('native', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'core', ['Distribution'])

        # Adding model 'CopyrightHolder'
        db.create_table(u'core_copyrightholder', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('coded_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('expanded_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('copyright', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('contact_info', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('primary_bds', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('date_record', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('permission_source', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('permission_level', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('permission_location', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('notes', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal(u'core', ['CopyrightHolder'])

        # Adding model 'Video'
        db.create_table(u'core_video', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('youtube_id', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'core', ['Video'])


    def backwards(self, orm):
        # Removing unique constraint on 'PlantPreviewCharacter', fields ['pile', 'character', 'partner_site']
        db.delete_unique(u'core_plantpreviewcharacter', ['pile_id', 'character_id', 'partner_site_id'])

        # Removing unique constraint on 'PartnerSpecies', fields ['species', 'partner']
        db.delete_unique(u'core_partnerspecies', ['species_id', 'partner_id'])

        # Removing unique constraint on 'DefaultFilter', fields ['key', 'pile', 'character']
        db.delete_unique(u'core_defaultfilter', ['key', 'pile_id', 'character_id'])

        # Removing unique constraint on 'ConservationLabel', fields ['taxon', 'region', 'label']
        db.delete_unique(u'core_conservationlabel', ['taxon_id', 'region', 'label'])

        # Removing unique constraint on 'TaxonCharacterValue', fields ['taxon', 'character_value']
        db.delete_unique(u'core_taxoncharactervalue', ['taxon_id', 'character_value_id'])

        # Removing unique constraint on 'GlossaryTerm', fields ['term', 'lay_definition']
        db.delete_unique(u'core_glossaryterm', ['term', 'lay_definition'])

        # Deleting model 'Parameter'
        db.delete_table(u'core_parameter')

        # Deleting model 'CharacterGroup'
        db.delete_table(u'core_charactergroup')

        # Deleting model 'GlossaryTerm'
        db.delete_table(u'core_glossaryterm')

        # Deleting model 'Character'
        db.delete_table(u'core_character')

        # Deleting model 'CharacterValue'
        db.delete_table(u'core_charactervalue')

        # Deleting model 'Pile'
        db.delete_table(u'core_pile')

        # Removing M2M table for field species on 'Pile'
        db.delete_table('core_pile_species')

        # Deleting model 'PileImage'
        db.delete_table(u'core_pileimage')

        # Deleting model 'PileGroup'
        db.delete_table(u'core_pilegroup')

        # Deleting model 'PileGroupImage'
        db.delete_table(u'core_pilegroupimage')

        # Deleting model 'ImageType'
        db.delete_table(u'core_imagetype')

        # Deleting model 'ContentImage'
        db.delete_table(u'core_contentimage')

        # Deleting model 'HomePageImage'
        db.delete_table(u'core_homepageimage')

        # Deleting model 'Family'
        db.delete_table(u'core_family')

        # Deleting model 'Genus'
        db.delete_table(u'core_genus')

        # Deleting model 'Synonym'
        db.delete_table(u'core_synonym')

        # Deleting model 'CommonName'
        db.delete_table(u'core_commonname')

        # Deleting model 'Lookalike'
        db.delete_table(u'core_lookalike')

        # Deleting model 'WetlandIndicator'
        db.delete_table(u'core_wetlandindicator')

        # Deleting model 'Taxon'
        db.delete_table(u'core_taxon')

        # Removing M2M table for field piles on 'Taxon'
        #db.delete_table('core_pile_species')

        # Deleting model 'SourceCitation'
        db.delete_table(u'core_sourcecitation')

        # Deleting model 'TaxonCharacterValue'
        db.delete_table(u'core_taxoncharactervalue')

        # Deleting model 'Edit'
        db.delete_table(u'core_edit')

        # Deleting model 'ConservationLabel'
        db.delete_table(u'core_conservationlabel')

        # Deleting model 'ConservationStatus'
        db.delete_table(u'core_conservationstatus')

        # Deleting model 'DefaultFilter'
        db.delete_table(u'core_defaultfilter')

        # Deleting model 'PartnerSite'
        db.delete_table(u'core_partnersite')

        # Removing M2M table for field users on 'PartnerSite'
        db.delete_table('core_partnersite_users')

        # Deleting model 'PartnerSpecies'
        db.delete_table(u'core_partnerspecies')

        # Deleting model 'PlantPreviewCharacter'
        db.delete_table(u'core_plantpreviewcharacter')

        # Deleting model 'Distribution'
        db.delete_table(u'core_distribution')

        # Deleting model 'CopyrightHolder'
        db.delete_table(u'core_copyrightholder')

        # Deleting model 'Video'
        db.delete_table(u'core_video')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.character': {
            'Meta': {'ordering': "['short_name']", 'object_name': 'Character'},
            'character_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.CharacterGroup']"}),
            'ease_of_observability': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'friendly_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'hint': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'pile': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'characters'", 'null': 'True', 'to': u"orm['core.Pile']"}),
            'question': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'value_type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'core.charactergroup': {
            'Meta': {'ordering': "['name']", 'object_name': 'CharacterGroup'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'core.charactervalue': {
            'Meta': {'object_name': 'CharacterValue'},
            'character': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'character_values'", 'to': u"orm['core.Character']"}),
            'friendly_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'value_flt': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_max': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_min': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'value_str': ('django.db.models.fields.CharField', [], {'max_length': '260', 'null': 'True', 'blank': 'True'})
        },
        u'core.commonname': {
            'Meta': {'ordering': "['common_name']", 'object_name': 'CommonName'},
            'common_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'taxon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'common_names'", 'to': u"orm['core.Taxon']"})
        },
        u'core.conservationlabel': {
            'Meta': {'ordering': "('taxon', 'region', 'label')", 'unique_together': "(('taxon', 'region', 'label'),)", 'object_name': 'ConservationLabel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'taxon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'conservation_labels'", 'to': u"orm['core.Taxon']"})
        },
        u'core.conservationstatus': {
            'Meta': {'object_name': 'ConservationStatus'},
            'allow_public_posting': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'endangerment_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            's_rank': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'taxon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'conservation_statuses'", 'to': u"orm['core.Taxon']"}),
            'variety_subspecies_hybrid': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        u'core.contentimage': {
            'Meta': {'object_name': 'ContentImage'},
            'alt': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'creator': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '300'}),
            'image_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.ImageType']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'rank': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'core.copyrightholder': {
            'Meta': {'object_name': 'CopyrightHolder'},
            'coded_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'contact_info': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'copyright': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'date_record': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'expanded_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'permission_level': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'permission_location': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'permission_source': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'primary_bds': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        u'core.defaultfilter': {
            'Meta': {'ordering': "['order']", 'unique_together': "(('key', 'pile', 'character'),)", 'object_name': 'DefaultFilter'},
            'character': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Character']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'pile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Pile']"})
        },
        u'core.distribution': {
            'Meta': {'ordering': "('scientific_name', 'state', 'county')", 'object_name': 'Distribution'},
            'county': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'native': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'present': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'scientific_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        u'core.edit': {
            'Meta': {'object_name': 'Edit'},
            'author': ('django.db.models.fields.TextField', [], {}),
            'coordinate1': ('django.db.models.fields.TextField', [], {}),
            'coordinate2': ('django.db.models.fields.TextField', [], {}),
            'datetime': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'itemtype': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'old_value': ('django.db.models.fields.TextField', [], {})
        },
        u'core.family': {
            'Meta': {'ordering': "['name']", 'object_name': 'Family'},
            'common_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'core.genus': {
            'Meta': {'ordering': "['name']", 'object_name': 'Genus'},
            'common_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'family': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'genera'", 'to': u"orm['core.Family']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'core.glossaryterm': {
            'Meta': {'unique_together': "(('term', 'lay_definition'),)", 'object_name': 'GlossaryTerm'},
            'highlight': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'lay_definition': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'term': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'core.homepageimage': {
            'Meta': {'ordering': "['image']", 'object_name': 'HomePageImage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'partner_site': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'home_page_images'", 'to': u"orm['core.PartnerSite']"})
        },
        u'core.imagetype': {
            'Meta': {'object_name': 'ImageType'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'core.lookalike': {
            'Meta': {'object_name': 'Lookalike'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lookalike_characteristic': ('django.db.models.fields.CharField', [], {'max_length': '900', 'blank': 'True'}),
            'lookalike_scientific_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'taxon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'lookalikes'", 'to': u"orm['core.Taxon']"})
        },
        u'core.parameter': {
            'Meta': {'ordering': "['name']", 'object_name': 'Parameter'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'value': ('django.db.models.fields.FloatField', [], {})
        },
        u'core.partnersite': {
            'Meta': {'ordering': "['short_name']", 'object_name': 'PartnerSite'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'species': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['core.Taxon']", 'through': u"orm['core.PartnerSpecies']", 'symmetrical': 'False'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'core.partnerspecies': {
            'Meta': {'unique_together': "(('species', 'partner'),)", 'object_name': 'PartnerSpecies'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.PartnerSite']"}),
            'simple_key': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'species': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Taxon']"}),
            'species_page_blurb': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'species_page_heading': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        u'core.pile': {
            'Meta': {'ordering': "['name']", 'object_name': 'Pile'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'friendly_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'friendly_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_characteristics': ('tinymce.models.HTMLField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'notable_exceptions': ('tinymce.models.HTMLField', [], {'blank': 'True'}),
            'pilegroup': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'piles'", 'null': 'True', 'to': u"orm['core.PileGroup']"}),
            'plant_preview_characters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'preview_characters'", 'symmetrical': 'False', 'through': u"orm['core.PlantPreviewCharacter']", 'to': u"orm['core.Character']"}),
            'sample_species_images': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sample_for_piles'", 'symmetrical': 'False', 'through': u"orm['core.PileImage']", 'to': u"orm['core.ContentImage']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'species': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'+'", 'symmetrical': 'False', 'to': u"orm['core.Taxon']"}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Video']", 'null': 'True'})
        },
        u'core.pilegroup': {
            'Meta': {'ordering': "['name']", 'object_name': 'PileGroup'},
            'friendly_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'friendly_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_characteristics': ('tinymce.models.HTMLField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'notable_exceptions': ('tinymce.models.HTMLField', [], {'blank': 'True'}),
            'sample_species_images': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'sample_for_pilegroups'", 'symmetrical': 'False', 'through': u"orm['core.PileGroupImage']", 'to': u"orm['core.ContentImage']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Video']", 'null': 'True'})
        },
        u'core.pilegroupimage': {
            'Meta': {'ordering': "['order']", 'object_name': 'PileGroupImage'},
            'content_image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.ContentImage']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'pile_group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.PileGroup']"})
        },
        u'core.pileimage': {
            'Meta': {'ordering': "['order']", 'object_name': 'PileImage'},
            'content_image': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.ContentImage']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'pile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Pile']"})
        },
        u'core.plantpreviewcharacter': {
            'Meta': {'ordering': "('partner_site', 'order')", 'unique_together': "(('pile', 'character', 'partner_site'),)", 'object_name': 'PlantPreviewCharacter'},
            'character': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Character']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'partner_site': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.PartnerSite']", 'null': 'True', 'blank': 'True'}),
            'pile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Pile']"})
        },
        u'core.sourcecitation': {
            'Meta': {'object_name': 'SourceCitation'},
            'article_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'citation_text': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'publication_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'publication_year': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'publisher_location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'publisher_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'core.synonym': {
            'Meta': {'ordering': "['scientific_name']", 'object_name': 'Synonym'},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scientific_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'taxon': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'synonyms'", 'to': u"orm['core.Taxon']"})
        },
        u'core.taxon': {
            'Meta': {'ordering': "['scientific_name']", 'object_name': 'Taxon'},
            'character_values': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['core.CharacterValue']", 'through': u"orm['core.TaxonCharacterValue']", 'symmetrical': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'factoid': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'family': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taxa'", 'to': u"orm['core.Family']"}),
            'genus': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taxa'", 'to': u"orm['core.Genus']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'north_american_introduced': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'north_american_native': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'piles': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'+'", 'blank': 'True', 'to': u"orm['core.Pile']"}),
            'scientific_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'taxonomic_authority': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'variety_notes': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'wetland_indicator_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        },
        u'core.taxoncharactervalue': {
            'Meta': {'unique_together': "(('taxon', 'character_value'),)", 'object_name': 'TaxonCharacterValue'},
            'character_value': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taxon_character_values'", 'to': u"orm['core.CharacterValue']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'literary_source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taxon_character_values'", 'null': 'True', 'to': u"orm['core.SourceCitation']"}),
            'taxon': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.Taxon']"})
        },
        u'core.video': {
            'Meta': {'object_name': 'Video'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'youtube_id': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'core.wetlandindicator': {
            'Meta': {'ordering': "['sequence']", 'object_name': 'WetlandIndicator'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '15'}),
            'friendly_description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['core']
