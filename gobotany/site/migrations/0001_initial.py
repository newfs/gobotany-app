# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PlantNameSuggestion'
        db.create_table(u'site_plantnamesuggestion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=150, db_index=True)),
        ))
        db.send_create_signal(u'site', ['PlantNameSuggestion'])

        # Adding model 'SearchSuggestion'
        db.create_table(u'site_searchsuggestion', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('term', self.gf('django.db.models.fields.CharField')(unique=True, max_length=150, db_index=True)),
        ))
        db.send_create_signal(u'site', ['SearchSuggestion'])


    def backwards(self, orm):
        # Deleting model 'PlantNameSuggestion'
        db.delete_table(u'site_plantnamesuggestion')

        # Deleting model 'SearchSuggestion'
        db.delete_table(u'site_searchsuggestion')


    models = {
        u'site.plantnamesuggestion': {
            'Meta': {'object_name': 'PlantNameSuggestion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150', 'db_index': 'True'})
        },
        u'site.searchsuggestion': {
            'Meta': {'object_name': 'SearchSuggestion'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'term': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150', 'db_index': 'True'})
        }
    }

    complete_apps = ['site']