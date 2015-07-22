# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Page'
        db.create_table(u'dkey_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chapter', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('title', self.gf('django.db.models.fields.TextField')(unique=True)),
            ('rank', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('text', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'dkey', ['Page'])

        # Adding M2M table for field breadcrumb_cache on 'Page'
        db.create_table(u'dkey_page_breadcrumb_cache', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_page', models.ForeignKey(orm[u'dkey.page'], null=False)),
            ('to_page', models.ForeignKey(orm[u'dkey.page'], null=False))
        ))
        db.create_unique(u'dkey_page_breadcrumb_cache', ['from_page_id', 'to_page_id'])

        # Adding model 'Lead'
        db.create_table(u'dkey_lead', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='leads', to=orm['dkey.Page'])),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='children', null=True, to=orm['dkey.Lead'])),
            ('letter', self.gf('django.db.models.fields.TextField')()),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('goto_page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='leadins', null=True, to=orm['dkey.Page'])),
            ('goto_num', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('taxa_cache', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'dkey', ['Lead'])

        # Adding model 'Hybrid'
        db.create_table(u'dkey_hybrid', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number1', self.gf('django.db.models.fields.IntegerField')()),
            ('number2', self.gf('django.db.models.fields.IntegerField')()),
            ('scientific_name1', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('scientific_name2', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('text', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'dkey', ['Hybrid'])

        # Adding model 'Figure'
        db.create_table(u'dkey_figure', (
            ('number', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('caption', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'dkey', ['Figure'])

        # Adding model 'IllustrativeSpecies'
        db.create_table(u'dkey_illustrativespecies', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group_number', self.gf('django.db.models.fields.IntegerField')()),
            ('family_name', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('species_name', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'dkey', ['IllustrativeSpecies'])


    def backwards(self, orm):
        # Deleting model 'Page'
        db.delete_table(u'dkey_page')

        # Removing M2M table for field breadcrumb_cache on 'Page'
        db.delete_table('dkey_page_breadcrumb_cache')

        # Deleting model 'Lead'
        db.delete_table(u'dkey_lead')

        # Deleting model 'Hybrid'
        db.delete_table(u'dkey_hybrid')

        # Deleting model 'Figure'
        db.delete_table(u'dkey_figure')

        # Deleting model 'IllustrativeSpecies'
        db.delete_table(u'dkey_illustrativespecies')


    models = {
        u'dkey.figure': {
            'Meta': {'object_name': 'Figure'},
            'caption': ('django.db.models.fields.TextField', [], {}),
            'number': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        u'dkey.hybrid': {
            'Meta': {'object_name': 'Hybrid'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number1': ('django.db.models.fields.IntegerField', [], {}),
            'number2': ('django.db.models.fields.IntegerField', [], {}),
            'scientific_name1': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'scientific_name2': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'dkey.illustrativespecies': {
            'Meta': {'object_name': 'IllustrativeSpecies'},
            'family_name': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'group_number': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'species_name': ('django.db.models.fields.TextField', [], {})
        },
        u'dkey.lead': {
            'Meta': {'object_name': 'Lead'},
            'goto_num': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'goto_page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'leadins'", 'null': 'True', 'to': u"orm['dkey.Page']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter': ('django.db.models.fields.TextField', [], {}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'leads'", 'to': u"orm['dkey.Page']"}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'null': 'True', 'to': u"orm['dkey.Lead']"}),
            'taxa_cache': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        u'dkey.page': {
            'Meta': {'object_name': 'Page'},
            'breadcrumb_cache': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'ignore+'", 'symmetrical': 'False', 'to': u"orm['dkey.Page']"}),
            'chapter': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rank': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'unique': 'True'})
        }
    }

    complete_apps = ['dkey']