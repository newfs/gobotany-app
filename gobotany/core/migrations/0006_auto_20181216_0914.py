# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-12-16 14:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20180519_1746'),
    ]

    operations = [
        migrations.CreateModel(
            name='Update',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('description', models.CharField(max_length=1000)),
            ],
        ),
        migrations.AlterModelOptions(
            name='distribution',
            options={'verbose_name': 'Distribution record'},
        ),
        migrations.AlterField(
            model_name='character',
            name='unit',
            field=models.CharField(blank=True, choices=[('mm', 'Millimeters'), ('m', 'Meters'), ('cm', 'Centimeters')], max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='character',
            name='value_type',
            field=models.CharField(choices=[('TEXT', 'Textual'), ('LENGTH', 'Length'), ('RATIO', 'Ratio')], max_length=10),
        ),
    ]
