# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Figure',
            fields=[
                ('number', models.IntegerField(serialize=False, primary_key=True)),
                ('caption', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Hybrid',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number1', models.IntegerField()),
                ('number2', models.IntegerField()),
                ('scientific_name1', models.TextField(db_index=True)),
                ('scientific_name2', models.TextField(db_index=True)),
                ('text', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IllustrativeSpecies',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_number', models.IntegerField()),
                ('family_name', models.TextField(db_index=True)),
                ('species_name', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Lead',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('letter', models.TextField()),
                ('text', models.TextField()),
                ('goto_num', models.IntegerField(null=True)),
                ('taxa_cache', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('chapter', models.TextField(blank=True)),
                ('title', models.TextField(unique=True)),
                ('rank', models.TextField(db_index=True)),
                ('text', models.TextField(blank=True)),
                ('breadcrumb_cache', models.ManyToManyField(related_name='ignore+', to='dkey.Page')),
            ],
            options={
                'verbose_name': 'dichotomous key page',
                'verbose_name_plural': 'dichotomous key pages',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='lead',
            name='goto_page',
            field=models.ForeignKey(related_name='leadins', to='dkey.Page', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lead',
            name='page',
            field=models.ForeignKey(related_name='leads', to='dkey.Page'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lead',
            name='parent',
            field=models.ForeignKey(related_name='children', to='dkey.Lead', null=True),
            preserve_default=True,
        ),
    ]
