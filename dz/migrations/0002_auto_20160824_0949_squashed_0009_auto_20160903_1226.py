# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-03 10:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [(b'dz', '0002_auto_20160824_0949'), (b'dz', '0003_auto_20160824_1104'), (b'dz', '0004_auto_20160828_0112'), (b'dz', '0005_auto_20160829_1822'), (b'dz', '0006_auto_20160830_1745'), (b'dz', '0007_auto_20160903_1008'), (b'dz', '0008_schedule'), (b'dz', '0009_auto_20160903_1226')]

    dependencies = [
        ('dz', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user',
            field=models.OneToOneField(db_column='id', on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='dz_user', serialize=False, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterModelOptions(
            name='news',
            options={'permissions': [('crawl_news', 'Can crawl news'), ('view_news', 'Can only view news')], 'verbose_name': 'news', 'verbose_name_plural': 'newss'},
        ),
        migrations.AlterModelOptions(
            name='tip',
            options={'permissions': [('crawl_tips', 'Can crawl tips'), ('view_tips', 'Can only view tips')], 'verbose_name': 'tip', 'verbose_name_plural': 'tips'},
        ),
        migrations.AlterField(
            model_name='crawl',
            name='action',
            field=models.CharField(choices=[('news', 'news crawl'), ('tips', 'tips crawl')], db_index=True, max_length=6, verbose_name='crawl target'),
        ),
        migrations.AlterField(
            model_name='crawl',
            name='host',
            field=models.CharField(db_index=True, max_length=24, verbose_name='hostname'),
        ),
        migrations.AlterField(
            model_name='crawl',
            name='type',
            field=models.CharField(choices=[('manual', 'manual crawl'), ('auto', 'auto crawl')], db_index=True, max_length=8, verbose_name='crawl type'),
        ),
        migrations.AlterField(
            model_name='news',
            name='section',
            field=models.CharField(db_index=True, max_length=20, verbose_name='sport'),
        ),
        migrations.AlterField(
            model_name='news',
            name='subsection',
            field=models.CharField(db_index=True, max_length=80, verbose_name='liga'),
        ),
        migrations.AlterField(
            model_name='news',
            name='updated',
            field=models.DateTimeField(db_index=True, verbose_name='updated'),
        ),
        migrations.AlterField(
            model_name='tip',
            name='tipster',
            field=models.CharField(db_index=True, max_length=12, verbose_name='tipster'),
        ),
        migrations.AlterField(
            model_name='crawl',
            name='started',
            field=models.DateTimeField(null=True, verbose_name='started at'),
        ),
        migrations.RemoveField(
            model_name='crawl',
            name='news',
        ),
        migrations.RemoveField(
            model_name='crawl',
            name='tips',
        ),
        migrations.RemoveField(
            model_name='crawl',
            name='ipaddr',
        ),
        migrations.AddField(
            model_name='crawl',
            name='count',
            field=models.SmallIntegerField(default=0, verbose_name='no. of items'),
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.TimeField(verbose_name='start time')),
                ('action', models.CharField(choices=[(b'news', 'news crawl'), (b'tips', 'tips crawl')], max_length=6, verbose_name='action')),
            ],
        ),
        migrations.AlterModelOptions(
            name='schedule',
            options={'verbose_name': 'job', 'verbose_name_plural': 'schedule'},
        ),
    ]
