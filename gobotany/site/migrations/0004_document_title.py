# Generated by Django 3.0.14 on 2021-05-23 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site', '0003_auto_20210522_0809'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='title',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
