# Generated by Django 2.1.2 on 2018-10-25 09:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024, unique=True)),
                ('_keywords', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Live',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('live_id', models.CharField(max_length=1024, unique=True)),
                ('_messages', models.TextField(default='[]')),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024)),
                ('_nick_names', models.TextField()),
                ('is_star', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024, unique=True)),
            ],
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['name'], name='cba_team_name_fca97b_idx'),
        ),
        migrations.AddField(
            model_name='player',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cba.Team'),
        ),
        migrations.AddIndex(
            model_name='action',
            index=models.Index(fields=['name'], name='cba_action_name_b9e6af_idx'),
        ),
        migrations.AddIndex(
            model_name='player',
            index=models.Index(fields=['team'], name='cba_player_team_id_15874a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='player',
            unique_together={('team', 'name')},
        ),
    ]
