# Generated by Django 2.1.2 on 2018-10-26 18:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0016_auto_20181026_1758'),
    ]

    operations = [
        migrations.RenameField(
            model_name='streaming',
            old_name='url',
            new_name='_urls',
        ),
    ]
