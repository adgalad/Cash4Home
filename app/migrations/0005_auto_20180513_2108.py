# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-05-13 21:08
from __future__ import unicode_literals

import app.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20180513_1830'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountbelongsto',
            name='alias',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='accountbelongsto',
            name='email',
            field=models.EmailField(max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='accountbelongsto',
            name='id_number',
            field=models.IntegerField(null=True, verbose_name='ID number'),
        ),
        migrations.AddField(
            model_name='accountbelongsto',
            name='owner',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='id_back',
            field=models.ImageField(null=True, upload_to=app.models.get_image_path),
        ),
        migrations.AlterField(
            model_name='user',
            name='id_front',
            field=models.ImageField(null=True, upload_to=app.models.get_image_path),
        ),
        migrations.AlterField(
            model_name='user',
            name='selfie_image',
            field=models.ImageField(null=True, upload_to=app.models.get_image_path),
        ),
        migrations.AlterField(
            model_name='user',
            name='service_image',
            field=models.ImageField(null=True, upload_to=app.models.get_image_path),
        ),
    ]
