# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import tinymce.models
import django.core.validators
import gobotany.core.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(unique=True, max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('friendly_name', models.CharField(max_length=100)),
                ('ease_of_observability', models.PositiveSmallIntegerField(blank=True, null=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('value_type', models.CharField(max_length=10, choices=[('TEXT', 'Textual'), ('LENGTH', 'Length'), ('RATIO', 'Ratio')])),
                ('unit', models.CharField(blank=True, max_length=2, null=True, choices=[('mm', 'Millimeters'), ('m', 'Meters'), ('cm', 'Centimeters')])),
                ('question', models.TextField(blank=True)),
                ('hint', models.TextField(blank=True)),
                ('image', models.ImageField(null=True, upload_to=b'character-value-images', blank=True)),
            ],
            options={
                'ordering': ['short_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CharacterGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CharacterValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_str', models.CharField(max_length=260, null=True, blank=True)),
                ('value_min', models.FloatField(null=True, blank=True)),
                ('value_max', models.FloatField(null=True, blank=True)),
                ('value_flt', models.FloatField(null=True, blank=True)),
                ('friendly_text', models.TextField(blank=True)),
                ('image', models.ImageField(null=True, upload_to=b'character-value-images', blank=True)),
                ('character', models.ForeignKey(related_name='character_values', to='core.Character')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CommonName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('common_name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['common_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConservationStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('variety_subspecies_hybrid', models.CharField(max_length=80, blank=True)),
                ('region', models.CharField(max_length=80, choices=[(b'CT', 'Connecticut'), (b'ME', 'Maine'), (b'MA', 'Massachusetts'), (b'NH', 'New Hampshire'), (b'RI', 'Rhode Island'), (b'VT', 'Vermont')])),
                ('s_rank', models.CharField(max_length=10, blank=True)),
                ('endangerment_code', models.CharField(max_length=10, blank=True)),
                ('allow_public_posting', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('taxon', 'variety_subspecies_hybrid', 'region'),
                'verbose_name': 'conservation status',
                'verbose_name_plural': 'conservation statuses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ContentImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(help_text=b'Image will be renamed and moved based on other field information.', upload_to=gobotany.core.models._content_image_path, max_length=300, verbose_name=b'content image')),
                ('alt', models.CharField(max_length=300, verbose_name='title (alt text)')),
                ('rank', models.PositiveSmallIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)])),
                ('creator', models.CharField(max_length=100, verbose_name='photographer')),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CopyrightHolder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('coded_name', models.CharField(unique=True, max_length=50)),
                ('expanded_name', models.CharField(max_length=100)),
                ('copyright', models.CharField(max_length=300)),
                ('source', models.CharField(max_length=300)),
                ('contact_info', models.CharField(max_length=300)),
                ('primary_bds', models.CharField(max_length=300)),
                ('date_record', models.CharField(max_length=300)),
                ('last_name', models.CharField(max_length=300)),
                ('permission_source', models.CharField(max_length=300)),
                ('permission_level', models.CharField(max_length=300)),
                ('permission_location', models.CharField(max_length=300)),
                ('notes', models.CharField(max_length=1000)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DefaultFilter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=36)),
                ('order', models.IntegerField()),
                ('character', models.ForeignKey(to='core.Character', null=True)),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('scientific_name', models.CharField(max_length=100, db_index=True)),
                ('species_name', models.CharField(default=b'', max_length=60, db_index=True)),
                ('subspecific_epithet', models.CharField(default=b'', max_length=60, db_index=True)),
                ('state', models.CharField(max_length=2, db_index=True)),
                ('county', models.CharField(max_length=50, blank=True)),
                ('present', models.BooleanField(default=False)),
                ('native', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('scientific_name', 'state', 'county'),
                'verbose_name': 'Distribution record',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Edit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.TextField()),
                ('datetime', models.DateTimeField()),
                ('itemtype', models.TextField(db_index=True)),
                ('coordinate1', models.TextField()),
                ('coordinate2', models.TextField()),
                ('old_value', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Family',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('common_name', models.CharField(max_length=100)),
                ('description', models.TextField(verbose_name='description', blank=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'family',
                'verbose_name_plural': 'families',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Genus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('common_name', models.CharField(max_length=100)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('family', models.ForeignKey(related_name='genera', to='core.Family')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'genus',
                'verbose_name_plural': 'genera',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GlossaryTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.CharField(max_length=100)),
                ('lay_definition', models.TextField(blank=True)),
                ('visible', models.BooleanField(default=True)),
                ('highlight', models.BooleanField(default=True)),
                ('image', models.ImageField(null=True, upload_to=b'glossary-images', blank=True)),
            ],
            options={
                'verbose_name': 'glossary term',
                'verbose_name_plural': 'glossary terms',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HomePageImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to=gobotany.core.models._partner_subdirectory_path)),
            ],
            options={
                'ordering': ['partner_site', 'image'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImageType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name='image type')),
                ('code', models.CharField(max_length=4, verbose_name='type code')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InvasiveStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('region', models.CharField(max_length=80, choices=[(b'ct', 'Connecticut'), (b'ma', 'Massachusetts'), (b'me', 'Maine'), (b'nh', 'New Hampshire'), (b'ri', 'Rhode Island'), (b'vt', 'Vermont')])),
                ('invasive_in_region', models.NullBooleanField(default=None)),
                ('prohibited_from_sale', models.NullBooleanField(default=None)),
            ],
            options={
                'ordering': ('taxon', 'region'),
                'verbose_name': 'invasive status',
                'verbose_name_plural': 'invasive statuses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Lookalike',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('lookalike_scientific_name', models.CharField(max_length=100)),
                ('lookalike_characteristic', models.CharField(max_length=1000, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('value', models.FloatField()),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PartnerSite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short_name', models.CharField(max_length=30)),
            ],
            options={
                'ordering': ['short_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PartnerSpecies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('simple_key', models.BooleanField(default=True)),
                ('species_page_heading', models.CharField(max_length=128, null=True, blank=True)),
                ('species_page_blurb', models.TextField(null=True, blank=True)),
                ('partner', models.ForeignKey(to='core.PartnerSite')),
            ],
            options={
                'verbose_name': 'Partner species',
                'verbose_name_plural': 'Partner species list',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Pile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.SlugField(unique=True, max_length=100)),
                ('friendly_name', models.CharField(max_length=100, blank=True)),
                ('friendly_title', models.CharField(max_length=100, blank=True)),
                ('key_characteristics', tinymce.models.HTMLField(blank=True)),
                ('notable_exceptions', tinymce.models.HTMLField(blank=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PileGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.SlugField(unique=True, max_length=100)),
                ('friendly_name', models.CharField(max_length=100, blank=True)),
                ('friendly_title', models.CharField(max_length=100, blank=True)),
                ('key_characteristics', tinymce.models.HTMLField(blank=True)),
                ('notable_exceptions', tinymce.models.HTMLField(blank=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PileGroupImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(null=True)),
                ('content_image', models.ForeignKey(to='core.ContentImage')),
                ('pile_group', models.ForeignKey(to='core.PileGroup')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PileImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField(null=True)),
                ('content_image', models.ForeignKey(to='core.ContentImage')),
                ('pile', models.ForeignKey(to='core.Pile')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlantPreviewCharacter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.IntegerField()),
                ('character', models.ForeignKey(to='core.Character')),
                ('partner_site', models.ForeignKey(blank=True, to='core.PartnerSite', null=True)),
                ('pile', models.ForeignKey(to='core.Pile')),
            ],
            options={
                'ordering': ('partner_site', 'order'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourceCitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('citation_text', models.CharField(max_length=300)),
                ('author', models.CharField(max_length=100, verbose_name='Author or Editor', blank=True)),
                ('publication_year', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Publication Year', validators=[django.core.validators.MaxValueValidator(2015)])),
                ('article_title', models.CharField(max_length=100, verbose_name='Article Title', blank=True)),
                ('publication_title', models.CharField(max_length=100, verbose_name='Periodical or Book Title', blank=True)),
                ('publisher_name', models.CharField(max_length=100, verbose_name='Publisher Name', blank=True)),
                ('publisher_location', models.CharField(max_length=100, verbose_name='Publisher Location', blank=True)),
            ],
            options={
                'ordering': ['citation_text'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Synonym',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('scientific_name', models.CharField(max_length=100)),
                ('full_name', models.CharField(max_length=150)),
            ],
            options={
                'ordering': ['scientific_name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Taxon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('scientific_name', models.CharField(unique=True, max_length=100)),
                ('taxonomic_authority', models.CharField(max_length=100)),
                ('factoid', models.CharField(max_length=1000, blank=True)),
                ('wetland_indicator_code', models.CharField(max_length=15, null=True, blank=True)),
                ('north_american_native', models.NullBooleanField()),
                ('north_american_introduced', models.NullBooleanField()),
                ('description', models.CharField(max_length=500, blank=True)),
                ('variety_notes', models.CharField(max_length=1000, blank=True)),
            ],
            options={
                'ordering': ['scientific_name'],
                'verbose_name': 'taxon',
                'verbose_name_plural': 'taxa',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaxonCharacterValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('character_value', models.ForeignKey(related_name='taxon_character_values', to='core.CharacterValue')),
                ('literary_source', models.ForeignKey(related_name='taxon_character_values', to='core.SourceCitation', null=True)),
                ('taxon', models.ForeignKey(to='core.Taxon')),
            ],
            options={
                'verbose_name': 'taxon character value',
                'verbose_name_plural': 'character values for taxon',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('youtube_id', models.CharField(max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WetlandIndicator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=15)),
                ('name', models.CharField(max_length=50)),
                ('friendly_description', models.CharField(max_length=200)),
                ('sequence', models.IntegerField()),
            ],
            options={
                'ordering': ['sequence'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='taxoncharactervalue',
            unique_together=set([('taxon', 'character_value')]),
        ),
        migrations.AddField(
            model_name='taxon',
            name='character_values',
            field=models.ManyToManyField(to='core.CharacterValue', through='core.TaxonCharacterValue'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxon',
            name='family',
            field=models.ForeignKey(related_name='taxa', to='core.Family'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxon',
            name='genus',
            field=models.ForeignKey(related_name='taxa', to='core.Genus'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='taxon',
            name='piles',
            field=models.ManyToManyField(related_name='+', to='core.Pile', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='synonym',
            name='taxon',
            field=models.ForeignKey(related_name='synonyms', to='core.Taxon'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='plantpreviewcharacter',
            unique_together=set([('pile', 'character', 'partner_site')]),
        ),
        migrations.AddField(
            model_name='pilegroup',
            name='sample_species_images',
            field=models.ManyToManyField(related_name='sample_for_pilegroups', through='core.PileGroupImage', to='core.ContentImage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pilegroup',
            name='video',
            field=models.ForeignKey(to='core.Video', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pile',
            name='pilegroup',
            field=models.ForeignKey(related_name='piles', to='core.PileGroup', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pile',
            name='plant_preview_characters',
            field=models.ManyToManyField(related_name='preview_characters', through='core.PlantPreviewCharacter', to='core.Character'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pile',
            name='sample_species_images',
            field=models.ManyToManyField(related_name='sample_for_piles', through='core.PileImage', to='core.ContentImage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pile',
            name='species',
            field=models.ManyToManyField(related_name='+', to='core.Taxon'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pile',
            name='video',
            field=models.ForeignKey(to='core.Video', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='partnerspecies',
            name='species',
            field=models.ForeignKey(to='core.Taxon'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='partnerspecies',
            unique_together=set([('species', 'partner')]),
        ),
        migrations.AddField(
            model_name='partnersite',
            name='species',
            field=models.ManyToManyField(to='core.Taxon', through='core.PartnerSpecies'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='partnersite',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lookalike',
            name='taxon',
            field=models.ForeignKey(related_name='lookalikes', to='core.Taxon'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='invasivestatus',
            name='taxon',
            field=models.ForeignKey(related_name='invasive_statuses', to='core.Taxon'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='homepageimage',
            name='partner_site',
            field=models.ForeignKey(related_name='home_page_images', to='core.PartnerSite'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='glossaryterm',
            unique_together=set([('term', 'lay_definition')]),
        ),
        migrations.AddField(
            model_name='defaultfilter',
            name='pile',
            field=models.ForeignKey(to='core.Pile'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='defaultfilter',
            unique_together=set([('key', 'pile', 'character')]),
        ),
        migrations.AddField(
            model_name='contentimage',
            name='image_type',
            field=models.ForeignKey(verbose_name=b'image type', to='core.ImageType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='conservationstatus',
            name='taxon',
            field=models.ForeignKey(related_name='conservation_statuses', to='core.Taxon'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='commonname',
            name='taxon',
            field=models.ForeignKey(related_name='common_names', to='core.Taxon'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='character',
            name='character_group',
            field=models.ForeignKey(to='core.CharacterGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='character',
            name='pile',
            field=models.ForeignKey(related_name='characters', blank=True, to='core.Pile', null=True),
            preserve_default=True,
        ),
    ]
