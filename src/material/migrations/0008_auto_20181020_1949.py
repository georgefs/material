# Generated by Django 2.1.2 on 2018-10-20 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0007_auto_20181020_1906'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='preview_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
