# Generated by Django 2.0.2 on 2018-02-22 01:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_learningsite_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='digitalobject',
            name='name',
        ),
        migrations.AddField(
            model_name='digitalobject',
            name='datestamp',
            field=models.DateField(blank=True, null=True),
        ),
    ]
