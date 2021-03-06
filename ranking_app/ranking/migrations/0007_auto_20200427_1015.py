# Generated by Django 3.0.5 on 2020-04-27 01:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ranking', '0006_auto_20200426_1547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='content',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='詳細説明'),
        ),
        migrations.AlterField(
            model_name='content',
            name='maker',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True, verbose_name='作り手'),
        ),
    ]
