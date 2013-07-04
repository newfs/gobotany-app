# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PlantOfTheDay'
        db.create_table(u'plantoftheday_plantoftheday', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scientific_name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('partner_short_name', self.gf('django.db.models.fields.CharField')(max_length=30, db_index=True)),
            ('include', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('last_seen', self.gf('django.db.models.fields.DateField')(null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'plantoftheday', ['PlantOfTheDay'])

        # Adding unique constraint on 'PlantOfTheDay', fields ['scientific_name', 'partner_short_name']
        db.create_unique(u'plantoftheday_plantoftheday', ['scientific_name', 'partner_short_name'])


    def backwards(self, orm):
        # Removing unique constraint on 'PlantOfTheDay', fields ['scientific_name', 'partner_short_name']
        db.delete_unique(u'plantoftheday_plantoftheday', ['scientific_name', 'partner_short_name'])

        # Deleting model 'PlantOfTheDay'
        db.delete_table(u'plantoftheday_plantoftheday')


    models = {
        u'plantoftheday.plantoftheday': {
            'Meta': {'ordering': "['scientific_name', 'partner_short_name']", 'unique_together': "(('scientific_name', 'partner_short_name'),)", 'object_name': 'PlantOfTheDay'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'include': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_seen': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'partner_short_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'scientific_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        }
    }

    complete_apps = ['plantoftheday']