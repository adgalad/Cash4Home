# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-07-08 02:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalsettings',
            name='EMAIL_VALIDATION_EXPIRATION',
            field=models.IntegerField(default=180, verbose_name='Expiración del email de validación'),
        ),
        migrations.AlterField(
            model_name='globalsettings',
            name='OPERATION_TIMEOUT',
            field=models.IntegerField(default=90, verbose_name='Expiración de la operación'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.FloatField(verbose_name='Monto'),
        ),
    ]
