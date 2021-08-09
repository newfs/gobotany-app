# Generated by Django 3.0.14 on 2021-05-22 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site', '0002_document'),
    ]

    operations = [
        migrations.RenameField(
            model_name='document',
            old_name='uploaded_at',
            new_name='added_at',
        ),
        migrations.AlterField(
            model_name='document',
            name='upload',
            field=models.FileField(upload_to='docs/'),
        ),
    ]
