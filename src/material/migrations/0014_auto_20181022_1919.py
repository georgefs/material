# Generated by Django 2.0 on 2018-10-22 19:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0013_auto_20181022_1551'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streaming',
            name='url',
            field=models.CharField(blank=True, max_length=4096, null=True),
        ),
    ]
