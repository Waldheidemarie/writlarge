# Generated by Django 2.0.2 on 2018-03-05 16:29

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_auto_20180302_1422'),
    ]

    operations = [
        migrations.CreateModel(
            name='Audience',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='InstructionalLevel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.RemoveField(
            model_name='learningsite',
            name='instructional_level',
        ),
        migrations.AddField(
            model_name='learningsite',
            name='target_audience',
            field=models.ManyToManyField(blank=True, to='main.Audience'),
        ),
        migrations.AddField(
            model_name='learningsite',
            name='instructional_level',
            field=models.ManyToManyField(blank=True, to='main.InstructionalLevel'),
        ),
    ]
