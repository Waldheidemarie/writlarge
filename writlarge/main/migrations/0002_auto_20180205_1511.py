# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-02-05 20:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='archivalcollection',
            options={'ordering': ['title'], 'verbose_name': 'Archival Collection'},
        ),
        migrations.AlterModelOptions(
            name='archivalrespository',
            options={'ordering': ['title'], 'verbose_name': 'Archival Repository'},
        ),
    ]