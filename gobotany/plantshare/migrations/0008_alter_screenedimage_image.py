# Generated by Django 3.2.15 on 2022-11-11 00:36

from django.db import migrations
import gobotany.plantshare.models
import imagekit.models.fields
import storages.backends.s3boto3


class Migration(migrations.Migration):

    dependencies = [
        ('plantshare', '0007_auto_20210521_0655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='screenedimage',
            name='image',
            field=imagekit.models.fields.ProcessedImageField(storage=storages.backends.s3boto3.S3Boto3Storage(bucket='newfs', location='upload_images'), upload_to=gobotany.plantshare.models.rename_image_by_type),
        ),
    ]