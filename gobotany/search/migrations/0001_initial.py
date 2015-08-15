# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupsListPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('main_heading', models.CharField(max_length=100)),
                ('groups', models.ManyToManyField(to='core.PileGroup')),
            ],
            options={
                'verbose_name': 'groups list page',
                'verbose_name_plural': 'groups list pages',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PlainPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('url_path', models.CharField(max_length=100)),
                ('search_text', models.TextField()),
                ('videos', models.ManyToManyField(to='core.Video')),
            ],
            options={
                'verbose_name': 'plain page',
                'verbose_name_plural': 'plain pages',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubgroupResultsPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('main_heading', models.CharField(max_length=200)),
                ('subgroup', models.ForeignKey(to='core.Pile')),
            ],
            options={
                'verbose_name': 'subgroup results page',
                'verbose_name_plural': 'subgroup results pages',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubgroupsListPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('main_heading', models.CharField(max_length=100)),
                ('group', models.ForeignKey(to='core.PileGroup')),
            ],
            options={
                'verbose_name': 'subgroups list page',
                'verbose_name_plural': 'subgroups list pages',
            },
            bases=(models.Model,),
        ),
    ]
