# Generated by Django 2.1.2 on 2018-10-19 13:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0003_auto_20181019_1258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streaming',
            name='video',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='material.Video'),
        ),
    ]