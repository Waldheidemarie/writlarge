# Generated by Django 2.0.4 on 2018-04-17 20:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0023_auto_20180417_0936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningsite',
            name='children',
            field=models.ManyToManyField(blank=True, to='main.LearningSite'),
        ),
    ]
