# Generated by Django 2.1.2 on 2018-10-25 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0014_auto_20181022_1919'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='videos',
            field=models.ManyToManyField(to='material.Video'),
        ),
    ]
