# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-31 19:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dkey', '0004_auto_20190131_1357'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hybrid',
            name='number1',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='hybrid',
            name='number2',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
