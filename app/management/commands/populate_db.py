#!/usr/bin/env python
from app.models import *
from django.contrib.auth.models import Permission, Group, ContentType
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    args = ''
    help = 'Populate Database with the seed at /app/management/commands/populate_db.py'

    def _populate(self):
        Permission.objects.all().delete()
        ContentType.objects.all().delete()
        Group.objects.all().delete()

        user      = ContentType(app_label='admin', model='Usuarios')
        bank      = ContentType(app_label='admin', model='Bancos')
        account   = ContentType(app_label='admin', model='Cuentas')
        country   = ContentType(app_label='admin', model='Paises')
        holiday   = ContentType(app_label='admin', model='Feriados')
        operation = ContentType(app_label='admin', model='Operaciones')
        rate      = ContentType(app_label='admin', model='Tasas')
        currency  = ContentType(app_label='admin', model='Monedas')
        group     = ContentType(app_label='admin', model='Grupos')
        
        btc_price = ContentType(app_label='dashboard', model='BTC_Price')
        dashboard_operation = ContentType(app_label='dashboard', model='Operation')



        user.save()
        bank.save()
        account.save()
        country.save()
        holiday.save()
        operation.save()
        rate.save()
        currency.save()
        group.save()

        btc_price.save()
        dashboard_operation.save()
        
        add_user  = Permission(name='Crear',  codename='add_user',  content_type=user)
        edit_user = Permission(name='Editar', codename='edit_user', content_type=user)
        add_user.save()       
        edit_user.save()
        

        add_bank  = Permission(name='Crear',  codename='add_bank',  content_type=bank)
        edit_bank = Permission(name='Editar', codename='edit_bank', content_type=bank)
        add_bank.save()       
        edit_bank.save()       
        

        add_account  = Permission(name='Crear',  codename='add_account',  content_type=account)
        edit_account = Permission(name='Editar', codename='edit_account', content_type=account)
        add_account.save()       
        edit_account.save()
        

        add_country  = Permission(name='Crear',  codename='add_country',  content_type=country)
        edit_country = Permission(name='Editar', codename='edit_country', content_type=country)
        add_country.save()       
        edit_country.save()
        

        add_holiday  = Permission(name='Crear',  codename='add_holiday',  content_type=holiday)
        edit_holiday = Permission(name='Editar', codename='edit_holiday', content_type=holiday)
        add_holiday.save()       
        edit_holiday.save()
        

        add_operation  = Permission(name='Crear',  codename='add_operation',  content_type=operation)
        edit_operation = Permission(name='Editar', codename='edit_operation', content_type=operation)
        add_operation.save()       
        edit_operation.save()
        

        add_rate  = Permission(name='Crear',  codename='add_rate',  content_type=rate)
        edit_rate = Permission(name='Editar', codename='edit_rate', content_type=rate)
        add_rate.save()       
        edit_rate.save()
        

        add_group  = Permission(name='Crear',  codename='add_group',  content_type=group)
        edit_group = Permission(name='Editar', codename='edit_group', content_type=group)
        add_group.save()       
        edit_group.save()

        btc_price_p = Permission(name='Ver precio BTC', codename='btc_price', content_type=btc_price)
        operation_operator = Permission(name='Ver opearciones de los demás', codename='operation_operator', content_type=dashboard_operation)
        btc_price_p.save()
        operation_operator.save()


        client   = Group(name='Cliente')
        operator = Group(name='Operador')
        ally1    = Group(name='Aliado-1')
        ally2    = Group(name='Aliado-2')
        ally3    = Group(name='Aliado-3')

        client.save()
        operator.save()
        ally1.save()
        ally2.save()
        ally3.save()

        operator.permissions.add(edit_user)
        operator.permissions.add(btc_price)
        operator.permissions.add(operation_operator)




    def handle(self, *args, **options):
        self._populate()



    
    
    
