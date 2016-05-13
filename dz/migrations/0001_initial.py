# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-13 19:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Crawl',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='Job Id')),
                ('type', models.CharField(choices=[('manual', 'manual'), ('auto', 'auto')], max_length=8)),
                ('action', models.CharField(choices=[('news', 'news'), ('tips', 'tips')], max_length=6, verbose_name='Target')),
                ('status', models.CharField(max_length=10)),
                ('started', models.DateTimeField(verbose_name='Started At')),
                ('ended', models.DateTimeField(null=True, verbose_name='Ended At')),
                ('news', models.SmallIntegerField(verbose_name='No. Of News')),
                ('tips', models.SmallIntegerField(verbose_name='No. Of Tips')),
                ('host', models.CharField(max_length=24, verbose_name='Hostname')),
                ('ipaddr', models.CharField(max_length=20, verbose_name='IP Address')),
                ('pid', models.CharField(max_length=6, verbose_name='PID')),
            ],
        ),
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.IntegerField(db_column='pk', primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(verbose_name='Link')),
                ('title', models.CharField(max_length=150, verbose_name='Title')),
                ('short_title', models.CharField(max_length=80, verbose_name='Participants')),
                ('section', models.CharField(max_length=20, verbose_name='Sport')),
                ('subsection', models.CharField(max_length=80, verbose_name='Liga')),
                ('published', models.DateTimeField(verbose_name='Published')),
                ('updated', models.DateTimeField(verbose_name='Updated')),
                ('crawled', models.DateTimeField(verbose_name='Fetched')),
                ('archived', models.CharField(choices=[('archived', 'archived'), ('fresh', 'fresh')], max_length=9, verbose_name='Archived')),
                ('preamble', models.CharField(max_length=500, null=True)),
                ('content', models.TextField(verbose_name='Full Content')),
                ('subtable', models.TextField(verbose_name='Subtable')),
            ],
            options={
                'verbose_name_plural': 'news',
            },
        ),
        migrations.CreateModel(
            name='Tip',
            fields=[
                ('id', models.IntegerField(db_column='pk', primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, verbose_name='Participants')),
                ('place', models.CharField(max_length=40, verbose_name='Liga')),
                ('tip', models.CharField(max_length=60, verbose_name='Title')),
                ('text', models.TextField(null=True, verbose_name='Text')),
                ('betting', models.CharField(max_length=32, verbose_name='Betting (Kladionica)')),
                ('coeff', models.CharField(max_length=6, verbose_name='Coeff. (Koeficijent)')),
                ('min_coeff', models.CharField(max_length=6, verbose_name='Min Coeff.')),
                ('result', models.CharField(max_length=15, verbose_name='Result (Rezultat)')),
                ('due', models.CharField(max_length=8, verbose_name='Earnings Due (Zarada)')),
                ('spread', models.CharField(max_length=8, verbose_name='Spread (Is. Margina)')),
                ('stake', models.CharField(max_length=8, verbose_name='Stake (Ulog)')),
                ('success', models.CharField(max_length=12, null=True, verbose_name='Success (Uspje\u0161nost)')),
                ('tipster', models.CharField(max_length=12, verbose_name='Tipster')),
                ('published', models.DateTimeField(null=True, verbose_name='Published (Objavleno)')),
                ('updated', models.DateTimeField(verbose_name='Updated')),
                ('crawled', models.DateTimeField(verbose_name='Fetched')),
                ('details_url', models.URLField(verbose_name='Link')),
                ('archived', models.CharField(choices=[('archived', 'archived'), ('fresh', 'fresh')], max_length=9)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=20, unique=True, verbose_name='User Name')),
                ('password', models.CharField(max_length=64, verbose_name='Password')),
                ('is_admin', models.BooleanField(verbose_name='Is Administrator')),
            ],
        ),
    ]
