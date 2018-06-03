# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-28 03:11
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_auto_20180527_2306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='code',
            field=models.CharField(max_length=100, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='mobile_phone',
            field=models.CharField(blank=True, max_length=16, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?\\d{9,15}$')], verbose_name='mobile phone'),
        ),
    ]
