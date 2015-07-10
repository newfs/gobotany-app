# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PlantOfTheDay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('scientific_name', models.CharField(max_length=100, db_index=True)),
                ('partner_short_name', models.CharField(max_length=30, db_index=True)),
                ('include', models.BooleanField(default=True)),
                ('last_seen', models.DateField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['scientific_name', 'partner_short_name'],
                'verbose_name': 'Plant of the Day',
                'verbose_name_plural': 'Plants of the Day',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='plantoftheday',
            unique_together=set([('scientific_name', 'partner_short_name')]),
        ),
    ]
