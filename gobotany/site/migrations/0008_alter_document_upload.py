# Generated by Django 3.2.15 on 2022-11-11 00:36

from django.db import migrations, models
import storages.backends.s3boto3


class Migration(migrations.Migration):

    dependencies = [
        ('site', '0007_auto_20210602_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='upload',
            field=models.FileField(storage=storages.backends.s3boto3.S3Boto3Storage(location='docs'), upload_to=''),
        ),
    ]