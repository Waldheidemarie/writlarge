# Generated by Django 2.0.4 on 2018-04-18 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0024_auto_20180417_1641'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningsite',
            name='corporate_body',
            field=models.TextField(blank=True, null=True),
        ),
    ]
