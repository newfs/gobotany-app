# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'SharingGroup'
        db.delete_table('plantshare_sharinggroup')

        # Deleting model 'SharingGroupMember'
        db.delete_table('plantshare_sharinggroupmember')

        # Adding model 'Pod'
        db.create_table('plantshare_pod', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('plantshare', ['Pod'])

        # Adding model 'PodMembership'
        db.create_table('plantshare_podmembership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plantshare.UserProfile'])),
            ('pod', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plantshare.Pod'])),
            ('is_owner', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_self_pod', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('plantshare', ['PodMembership'])


    def backwards(self, orm):
        # Adding model 'SharingGroup'
        db.create_table('plantshare_sharinggroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('plantshare', ['SharingGroup'])

        # Adding model 'SharingGroupMember'
        db.create_table('plantshare_sharinggroupmember', (
            ('member', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plantshare.UserProfile'])),
            ('is_owner', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plantshare.SharingGroup'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('plantshare', ['SharingGroupMember'])

        # Deleting model 'Pod'
        db.delete_table('plantshare_pod')

        # Deleting model 'PodMembership'
        db.delete_table('plantshare_podmembership')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'plantshare.location': {
            'Meta': {'object_name': 'Location'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'user_input': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'plantshare.pod': {
            'Meta': {'object_name': 'Pod'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'pods'", 'symmetrical': 'False', 'through': "orm['plantshare.PodMembership']", 'to': "orm['plantshare.UserProfile']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'plantshare.podmembership': {
            'Meta': {'object_name': 'PodMembership'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_owner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_self_pod': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'member': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plantshare.UserProfile']"}),
            'pod': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plantshare.Pod']"})
        },
        'plantshare.question': {
            'Meta': {'object_name': 'Question'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '3000', 'blank': 'True'}),
            'answered': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'asked': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'asked_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'questions_asked'", 'to': "orm['auth.User']"}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'plantshare.screenedimage': {
            'Meta': {'object_name': 'ScreenedImage'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('imagekit.models.fields.ProcessedImageField', [], {'max_length': '100'}),
            'image_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'orphaned': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'screened': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'screened_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images_approved'", 'null': 'True', 'to': "orm['auth.User']"}),
            'uploaded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'uploaded_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images_uploaded'", 'to': "orm['auth.User']"})
        },
        'plantshare.sighting': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Sighting'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identification': ('django.db.models.fields.CharField', [], {'max_length': '120', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plantshare.Location']", 'null': 'True'}),
            'location_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'photos': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['plantshare.ScreenedImage']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'plantshare.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'avatar': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plantshare.ScreenedImage']", 'null': 'True', 'blank': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '60', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plantshare.Location']", 'null': 'True', 'blank': 'True'}),
            'location_visibility': ('django.db.models.fields.CharField', [], {'default': "'PRIVATE'", 'max_length': '7'}),
            'saying': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'security_answer': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'security_question': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'sharing_visibility': ('django.db.models.fields.CharField', [], {'default': "'PRIVATE'", 'max_length': '7'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'})
        }
    }

    complete_apps = ['plantshare']