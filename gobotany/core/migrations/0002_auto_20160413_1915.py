# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distribution',
            name='species_name',
            field=models.CharField(default=b'', max_length=60, db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='distribution',
            name='subspecific_epithet',
            field=models.CharField(default=b'', max_length=60, db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='sourcecitation',
            name='publication_year',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Publication Year', validators=[django.core.validators.MaxValueValidator(2016)]),
        ),
    ]
