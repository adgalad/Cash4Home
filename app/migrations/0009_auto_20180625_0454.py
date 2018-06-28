# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-06-25 04:54
from __future__ import unicode_literals

import app.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20180624_0315'),
    ]

    operations = [
        migrations.AddField(
            model_name='repurchase',
            name='exchanger',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='app.Exchanger'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='repurchase',
            name='profit',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='operation',
            name='account_allie_origin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='account_allie_origin', to='app.Account', verbose_name='Cuenta aliado origen'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='account_allie_target',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='account_allie_target', to='app.Account', verbose_name='Cuenta aliado origen'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='id_allie_origin',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_allie_origin', to=settings.AUTH_USER_MODEL, verbose_name='Aliado origen'),
        ),
        migrations.AlterField(
            model_name='operation',
            name='id_allie_target',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_allie_target', to=settings.AUTH_USER_MODEL, verbose_name='Aliado destino'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='date',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='id_operation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='app.Operation', verbose_name='Operación asociada'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='operation_type',
            field=models.CharField(choices=[('TO', 'TO'), ('TD', 'TD'), ('TC', 'TC')], max_length=3, verbose_name='Tipo de transacción'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='origin_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='origin_account', to='app.Account', verbose_name='Cuenta origen'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='target_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='target_account', to='app.Account', verbose_name='Cuenta destino'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='to_exchanger',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.Exchanger', verbose_name='Exchanger'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transfer_image',
            field=models.ImageField(upload_to=app.models.get_image_path, verbose_name='Imagen del comprobante'),
        ),
    ]