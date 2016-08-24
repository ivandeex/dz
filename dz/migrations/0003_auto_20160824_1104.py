# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-24 09:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dz', '0002_auto_20160824_0949'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='news',
            options={'permissions': [('crawl_news', 'Can crawl news'), ('view_news', 'Can only view news')], 'verbose_name': 'news', 'verbose_name_plural': 'newss'},
        ),
        migrations.AlterModelOptions(
            name='tip',
            options={'permissions': [('crawl_tips', 'Can crawl tips'), ('view_tips', 'Can only view tips')], 'verbose_name': 'tip', 'verbose_name_plural': 'tips'},
        ),
    ]