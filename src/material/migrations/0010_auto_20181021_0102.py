# Generated by Django 2.1.2 on 2018-10-21 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0009_streaming_meta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streaming',
            name='status',
            field=models.CharField(choices=[('init', 'init'), ('wait', 'wait'), ('live', 'live'), ('done', 'done'), ('fails', 'fails')], default='init', max_length=1024),
        ),
    ]
