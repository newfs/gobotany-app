# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('plantshare', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailaddress',
            name='email',
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name='question',
            name='images',
            field=models.ManyToManyField(to='plantshare.ScreenedImage', blank=True),
        ),
        migrations.AlterField(
            model_name='sighting',
            name='photos',
            field=models.ManyToManyField(to='plantshare.ScreenedImage', blank=True),
        ),
    ]
