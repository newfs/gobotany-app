# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import imagekit.models.fields
import django.core.files.storage
from django.conf import settings
import gobotany.plantshare.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Checklist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('comments', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChecklistCollaborator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_owner', models.BooleanField(default=False)),
                ('checklist', models.ForeignKey(to='plantshare.Checklist')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChecklistEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('plant_name', models.CharField(max_length=100)),
                ('is_checked', models.BooleanField(default=False)),
                ('location', models.CharField(max_length=100, blank=True)),
                ('date_found', models.DateTimeField(null=True, blank=True)),
                ('date_posted', models.DateTimeField(null=True, blank=True)),
                ('note', models.TextField(blank=True)),
                ('checklist', models.ForeignKey(related_name='entries', to='plantshare.Checklist')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EmailAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75)),
                ('verified', models.BooleanField(default=False)),
                ('primary', models.BooleanField(default=False)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'email address',
                'verbose_name_plural': 'email addresses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EmailConfirmation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sent', models.DateTimeField()),
                ('confirmation_key', models.CharField(max_length=40)),
                ('email_address', models.ForeignKey(to='plantshare.EmailAddress')),
            ],
            options={
                'verbose_name': 'email confirmation',
                'verbose_name_plural': 'email confirmations',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_input', models.CharField(max_length=255)),
                ('street', models.CharField(max_length=200, null=True, blank=True)),
                ('city', models.CharField(max_length=120, null=True, blank=True)),
                ('state', models.CharField(max_length=60, null=True, blank=True)),
                ('postal_code', models.CharField(max_length=12, null=True, blank=True)),
                ('latitude', models.FloatField(null=True, blank=True)),
                ('longitude', models.FloatField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Pod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PodMembership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_owner', models.BooleanField(default=False)),
                ('is_self_pod', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.CharField(max_length=500)),
                ('answer', models.CharField(max_length=3000, blank=True)),
                ('asked', models.DateTimeField(auto_now_add=True)),
                ('approved', models.BooleanField(default=False)),
                ('answered', models.DateTimeField(null=True, editable=False)),
                ('asked_by', models.ForeignKey(related_name='questions_asked', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'question',
                'verbose_name_plural': 'questions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ScreenedImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', imagekit.models.fields.ProcessedImageField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/media/upload_images/', location=b'/Users/john/Documents/dev/newfs/gobotany-app/gobotany/media/upload_images'), upload_to=gobotany.plantshare.models.rename_image_by_type)),
                ('uploaded', models.DateTimeField(auto_now_add=True)),
                ('image_type', models.CharField(blank=True, max_length=10, choices=[(b'AVATAR', b'User Avatar'), (b'SIGHTING', b'Sighting Photo'), (b'CHECKLIST', b'Checklist Photo'), (b'QUESTION', b'Question Photo')])),
                ('latitude', models.FloatField(null=True, blank=True)),
                ('longitude', models.FloatField(null=True, blank=True)),
                ('screened', models.DateTimeField(null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('orphaned', models.BooleanField(default=False)),
                ('deleted', models.BooleanField(default=False)),
                ('screened_by', models.ForeignKey(related_name='images_approved', to=settings.AUTH_USER_MODEL, null=True)),
                ('uploaded_by', models.ForeignKey(related_name='images_uploaded', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Sighting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField()),
                ('identification', models.CharField(max_length=120, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('location_notes', models.TextField(blank=True)),
                ('visibility', models.CharField(default=b'PUBLIC', max_length=7, choices=[(b'PUBLIC', b'Everyone: public'), (b'USERS', b'All PlantShare users'), (b'PRIVATE', b'Only you and PlantShare staff')])),
                ('flagged', models.BooleanField(default=False)),
                ('approved', models.BooleanField(default=False)),
                ('location', models.ForeignKey(to='plantshare.Location', null=True)),
                ('photos', models.ManyToManyField(to='plantshare.ScreenedImage', null=True, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'verbose_name': 'sighting',
                'verbose_name_plural': 'sightings',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('zipcode', models.CharField(max_length=5, blank=True)),
                ('security_question', models.CharField(max_length=100, blank=True)),
                ('security_answer', models.CharField(max_length=100, blank=True)),
                ('details_visibility', models.CharField(default=b'USERS', max_length=7, choices=[(b'USERS', b'All PlantShare users'), (b'PRIVATE', b'Only you and PlantShare staff')])),
                ('display_name', models.CharField(max_length=60, blank=True)),
                ('saying', models.CharField(max_length=100, blank=True)),
                ('location_visibility', models.CharField(default=b'USERS', max_length=7, choices=[(b'USERS', b'All PlantShare users'), (b'PRIVATE', b'Only you and PlantShare staff')])),
                ('avatar', models.ForeignKey(blank=True, to='plantshare.ScreenedImage', null=True)),
                ('location', models.ForeignKey(blank=True, to='plantshare.Location', null=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='question',
            name='images',
            field=models.ManyToManyField(to='plantshare.ScreenedImage', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='podmembership',
            name='member',
            field=models.ForeignKey(to='plantshare.UserProfile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='podmembership',
            name='pod',
            field=models.ForeignKey(to='plantshare.Pod'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pod',
            name='members',
            field=models.ManyToManyField(related_name='pods', through='plantshare.PodMembership', to='plantshare.UserProfile'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='emailaddress',
            unique_together=set([('user', 'email')]),
        ),
        migrations.AddField(
            model_name='checklistentry',
            name='plant_photo',
            field=models.ForeignKey(blank=True, to='plantshare.ScreenedImage', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='checklistcollaborator',
            name='collaborator',
            field=models.ForeignKey(to='plantshare.Pod'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='checklist',
            name='collaborators',
            field=models.ManyToManyField(related_name='checklists', through='plantshare.ChecklistCollaborator', to='plantshare.Pod'),
            preserve_default=True,
        ),
    ]
