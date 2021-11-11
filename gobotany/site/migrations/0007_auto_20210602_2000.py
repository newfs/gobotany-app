# Generated by Django 3.0.14 on 2021-06-03 00:00

import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site', '0006_auto_20210523_1311'),
    ]

    operations = [
        migrations.CreateModel(
            name='Highlight',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField()),
                ('active', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Update',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('description', models.TextField()),
                ('family', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.AlterField(
            model_name='document',
            name='upload',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url='/media/docs/', location='/Users/john/Documents/dev/newfs/gobotany-app/gobotany/media/docs'), upload_to=''),
        ),
    ]