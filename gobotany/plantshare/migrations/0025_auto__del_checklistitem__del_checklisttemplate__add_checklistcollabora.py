# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'ChecklistItem'
        db.delete_table('plantshare_checklistitem')

        # Deleting model 'ChecklistTemplate'
        db.delete_table('plantshare_checklisttemplate')

        # Removing M2M table for field viewer_pods on 'ChecklistTemplate'
        db.delete_table('plantshare_checklisttemplate_viewer_pods')

        # Adding model 'ChecklistCollaborator'
        db.create_table('plantshare_checklistcollaborator', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('collaborator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plantshare.Pod'])),
            ('checklist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plantshare.Checklist'])),
            ('is_owner', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('plantshare', ['ChecklistCollaborator'])

        # Adding model 'ChecklistEntry'
        db.create_table('plantshare_checklistentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('checklist', self.gf('django.db.models.fields.related.ForeignKey')(related_name='entries', to=orm['plantshare.Checklist'])),
            ('plant_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('is_checked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('plant_photo', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plantshare.ScreenedImage'], null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('date_found', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('date_posted', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('note', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('plantshare', ['ChecklistEntry'])

        # Deleting field 'Checklist.template'
        db.delete_column('plantshare_checklist', 'template_id')

        # Removing M2M table for field collaborators on 'Checklist'
        db.delete_table('plantshare_checklist_collaborators')


    def backwards(self, orm):
        # Adding model 'ChecklistItem'
        db.create_table('plantshare_checklistitem', (
            ('note', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('date_found', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['plantshare.ChecklistTemplate'])),
            ('plant_photo', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['plantshare.ScreenedImage'], null=True, blank=True)),
            ('plant_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('checklist', self.gf('django.db.models.fields.related.ForeignKey')(related_name='checked_items', null=True, to=orm['plantshare.Checklist'])),
            ('date_posted', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('plantshare', ['ChecklistItem'])

        # Adding model 'ChecklistTemplate'
        db.create_table('plantshare_checklisttemplate', (
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='owned_checklist_templates', to=orm['plantshare.UserProfile'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_checklist_templates', to=orm['plantshare.UserProfile'])),
        ))
        db.send_create_signal('plantshare', ['ChecklistTemplate'])

        # Adding M2M table for field viewer_pods on 'ChecklistTemplate'
        db.create_table('plantshare_checklisttemplate_viewer_pods', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('checklisttemplate', models.ForeignKey(orm['plantshare.checklisttemplate'], null=False)),
            ('pod', models.ForeignKey(orm['plantshare.pod'], null=False))
        ))
        db.create_unique('plantshare_checklisttemplate_viewer_pods', ['checklisttemplate_id', 'pod_id'])

        # Deleting model 'ChecklistCollaborator'
        db.delete_table('plantshare_checklistcollaborator')

        # Deleting model 'ChecklistEntry'
        db.delete_table('plantshare_checklistentry')

        # Adding field 'Checklist.template'
        db.add_column('plantshare_checklist', 'template',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['plantshare.ChecklistTemplate']),
                      keep_default=False)

        # Adding M2M table for field collaborators on 'Checklist'
        db.create_table('plantshare_checklist_collaborators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('checklist', models.ForeignKey(orm['plantshare.checklist'], null=False)),
            ('pod', models.ForeignKey(orm['plantshare.pod'], null=False))
        ))
        db.create_unique('plantshare_checklist_collaborators', ['checklist_id', 'pod_id'])


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
        'plantshare.checklist': {
            'Meta': {'object_name': 'Checklist'},
            'collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'checklists'", 'symmetrical': 'False', 'through': "orm['plantshare.ChecklistCollaborator']", 'to': "orm['plantshare.Pod']"}),
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'plantshare.checklistcollaborator': {
            'Meta': {'object_name': 'ChecklistCollaborator'},
            'checklist': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plantshare.Checklist']"}),
            'collaborator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plantshare.Pod']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_owner': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'plantshare.checklistentry': {
            'Meta': {'object_name': 'ChecklistEntry'},
            'checklist': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': "orm['plantshare.Checklist']"}),
            'date_found': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_posted': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_checked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'plant_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'plant_photo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['plantshare.ScreenedImage']", 'null': 'True', 'blank': 'True'})
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
            'category': ('django.db.models.fields.CharField', [], {'default': "'General'", 'max_length': '120'}),
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