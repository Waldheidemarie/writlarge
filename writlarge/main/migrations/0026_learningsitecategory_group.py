# Generated by Django 2.0.4 on 2018-04-19 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0025_learningsite_corporate_body'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningsitecategory',
            name='group',
            field=models.TextField(default='other'),
        ),
    ]