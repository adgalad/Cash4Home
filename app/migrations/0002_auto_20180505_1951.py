# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-05 19:51
from __future__ import unicode_literals

import app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.CharField(blank=True, max_length=64, verbose_name='address'),
        ),
        migrations.AddField(
            model_name='user',
            name='id_back',
            field=models.ImageField(blank=True, null=True, upload_to=app.models.get_image_path),
        ),
        migrations.AddField(
            model_name='user',
            name='id_front',
            field=models.ImageField(blank=True, null=True, upload_to=app.models.get_image_path),
        ),
        migrations.AddField(
            model_name='user',
            name='id_number',
            field=models.IntegerField(blank=True, default=0, verbose_name='ID number'),
        ),
        migrations.AddField(
            model_name='user',
            name='mobile_phone',
            field=models.CharField(blank=True, max_length=16, verbose_name='address'),
        ),
        migrations.AddField(
            model_name='user',
            name='selfie_image',
            field=models.ImageField(blank=True, null=True, upload_to=app.models.get_image_path),
        ),
        migrations.AddField(
            model_name='user',
            name='service_image',
            field=models.ImageField(blank=True, null=True, upload_to=app.models.get_image_path),
        ),
    ]
