# Generated by Django 3.0.5 on 2020-04-20 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ranking', '0002_auto_20200420_1735'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='tweet_id',
            field=models.CharField(max_length=100, unique=True, verbose_name='ツイートID'),
        ),
    ]