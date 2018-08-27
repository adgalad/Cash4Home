#!/usr/bin/env python
from app.models import *
from django.contrib.auth.models import Permission, Group, ContentType
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    args = ''
    help = 'Populate Database with the seed at /app/management/commands/populate_db.py'

    def _permissions(self):
        Permission.objects.all().delete()
        ContentType.objects.all().delete()
        Group.objects.all().delete()

        user        = ContentType(app_label='admin', model='Usuarios')
        bank        = ContentType(app_label='admin', model='Bancos')
        account     = ContentType(app_label='admin', model='Cuentas')
        country     = ContentType(app_label='admin', model='Paises')
        closure     = ContentType(app_label='admin', model='Cierre')
        holiday     = ContentType(app_label='admin', model='Feriados')
        operation   = ContentType(app_label='admin', model='Operaciones')
        transaction = ContentType(app_label='admin', model='Transacciones')
        rate        = ContentType(app_label='admin', model='Tasas')
        currency    = ContentType(app_label='admin', model='Monedas')
        group       = ContentType(app_label='admin', model='Grupos')
        exchanger   = ContentType(app_label='admin', model='Exchanger')
        repurchase  = ContentType(app_label='admin', model='Recompra')
        settings    = ContentType(app_label='admin', model='Configuración')
        
        btc_price = ContentType(app_label='dashboard', model='PrecioBTC')
        dashboard_operation = ContentType(app_label='dashboard', model='OperacionesDashboard')



        user.save()
        bank.save()
        account.save()
        country.save()
        closure.save()
        holiday.save()
        operation.save()
        transaction.save()
        rate.save()
        currency.save()
        group.save()
        exchanger.save()
        repurchase.save()
        settings.save()

        btc_price.save()
        dashboard_operation.save()
        
        add_user  = Permission(name='Crear',  codename='add_user',  content_type=user)
        view_user = Permission(name='Ver', codename='view_user', content_type=user)
        edit_user = Permission(name='Editar', codename='edit_user', content_type=user)
        add_user.save()       
        view_user.save()
        edit_user.save()
        

        add_bank  = Permission(name='Crear',  codename='add_bank',  content_type=bank)
        view_bank = Permission(name='Ver', codename='view_bank', content_type=bank)
        edit_bank = Permission(name='Editar', codename='edit_bank', content_type=bank)
        add_bank.save()       
        view_bank.save()
        edit_bank.save()       
        

        add_account  = Permission(name='Crear',  codename='add_account',  content_type=account)
        view_account = Permission(name='Ver', codename='view_account', content_type=account)
        edit_account = Permission(name='Editar', codename='edit_account', content_type=account)
        add_account.save()       
        view_account.save()
        edit_account.save()
        

        add_closure  = Permission(name='Crear',  codename='add_closure',  content_type=closure)
        view_closure = Permission(name='Ver', codename='view_closure', content_type=closure)
        edit_closure = Permission(name='Editar', codename='edit_closure', content_type=closure)
        add_closure.save()       
        view_closure.save()
        edit_closure.save()

        add_country  = Permission(name='Crear',  codename='add_country',  content_type=country)
        view_country = Permission(name='Ver', codename='view_country', content_type=country)
        edit_country = Permission(name='Editar', codename='edit_country', content_type=country)
        add_country.save()       
        view_country.save()
        edit_country.save()
        

        add_holiday  = Permission(name='Crear',  codename='add_holiday',  content_type=holiday)
        view_holiday = Permission(name='Ver', codename='view_holiday', content_type=holiday)
        edit_holiday = Permission(name='Editar', codename='edit_holiday', content_type=holiday)
        add_holiday.save()       
        view_holiday.save()
        edit_holiday.save()
        

        add_operation    = Permission(name='Crear',    codename='add_operation',    content_type=operation)
        view_operation   = Permission(name='Ver',      codename='view_operation',   content_type=operation)
        edit_operation   = Permission(name='Editar',   codename='edit_operation',   content_type=operation)
        cancel_operation = Permission(name='Cancelar', codename='cancel_operation', content_type=operation)
        coordinate_operation = Permission(name='Coordinar otras operaciones', codename='coordinate_operation', content_type=operation)
        add_operation.save()       
        view_operation.save()
        edit_operation.save()
        cancel_operation.save()
        coordinate_operation.save()
        
        add_transaction = Permission(name='Crear', codename='add_transaction', content_type=transaction)
        view_transaction = Permission(name='Ver', codename='view_transaction', content_type=transaction)
        add_transaction.save()
        view_transaction.save()

        add_rate  = Permission(name='Crear',  codename='add_rate',  content_type=rate)
        view_rate = Permission(name='Ver',    codename='view_rate', content_type=rate)
        edit_rate = Permission(name='Editar', codename='edit_rate', content_type=rate)
        add_rate.save()       
        view_rate.save()
        edit_rate.save()
        

        add_group  = Permission(name='Crear',  codename='add_group',  content_type=group)
        view_group = Permission(name='Ver',    codename='view_group', content_type=group)
        edit_group = Permission(name='Editar', codename='edit_group', content_type=group)
        add_group.save()       
        view_group.save()
        edit_group.save()

        edit_settings = Permission(name='Editar', codename='edit_settings', content_type=group)
        edit_settings.save()

        add_exchanger  = Permission(name='Crear',  codename='add_exchanger',  content_type=exchanger)
        view_exchanger = Permission(name='Ver',    codename='view_exchanger', content_type=exchanger)
        edit_exchanger = Permission(name='Editar', codename='edit_exchanger', content_type=exchanger)
        add_exchanger.save()       
        view_exchanger.save()
        edit_exchanger.save()

        add_repurchase  = Permission(name='Crear',  codename='add_repurchase',  content_type=repurchase)
        view_repurchase = Permission(name='Ver',    codename='view_repurchase', content_type=repurchase)
        edit_repurchase = Permission(name='Editar', codename='edit_repurchase', content_type=repurchase)
        add_repurchase.save()       
        view_repurchase.save()
        edit_repurchase.save()

        btc_price_p         = Permission(name='Ver precio BTC', codename='btc_price', content_type=btc_price)
        operations_operator = Permission(name='Ver dashboard de operaciones', codename='operations_operator', content_type=dashboard_operation)
        operations_all      = Permission(name='Ver todas las operaciones', codename='operations_all', content_type=dashboard_operation)
        btc_price_p.save()
        operations_operator.save()
        operations_all.save()


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
        operator.permissions.add(btc_price_p)
        operator.permissions.add(operations_operator)


    def _countries(self):
        Country(name="Argentina", iso_code="AR").save()
        Country(name="Bolivia",   iso_code="BO").save()
        Country(name="Brasil",    iso_code="BR").save()
        Country(name="Canada",    iso_code="CA").save()
        Country(name="Colombia",  iso_code="CO").save()
        Country(name="Chile",     iso_code="CL").save()
        Country(name="Ecuador",   iso_code="EC").save()
        Country(name="Estados Unidos", iso_code="US").save()
        Country(name="Mexico",    iso_code="MX").save()
        Country(name="Panama",    iso_code="PA").save()
        Country(name="Paraguay",  iso_code="PY").save()
        Country(name="Peru",      iso_code="PE").save()
        Country(name="Uruguay",   iso_code="UR").save()
        Country(name="Venezuela", iso_code="VE").save()
        Country(name="España",    iso_code="ES").save()

    def _currencies(self):
        
        Currency(name="Peso argentino",  code="ARS", currency_type="FIAT").save()
        Currency(name="Peso colombiano", code="COP", currency_type="FIAT").save()
        Currency(name="Peso mexicano",   code="MXN", currency_type="FIAT").save()
        Currency(name="Sol",             code="PEN", currency_type="FIAT").save()
        Currency(name="Dolar",           code="USD", currency_type="FIAT").save()
        Currency(name="Dolar canadiense", code="CAD", currency_type="FIAT").save()
        Currency(name="Euro",            code="EUR", currency_type="FIAT").save()
        Currency(name="Peso chileno",    code="CLP", currency_type="FIAT").save()
        Currency(name="Guaraní",         code="PYG", currency_type="FIAT").save()
        Currency(name="Peso uruguayo",   code="UYU", currency_type="FIAT").save()
        Currency(name="Bolívar",         code="VES", currency_type="FIAT").save()
        

        Currency(name="Bitcoin",  code="BTC",  currency_type="Crypto").save()
        Currency(name="Ethereum", code="ETH",  currency_type="Crypto").save()
        Currency(name="Litecoin", code="LTC",  currency_type="Crypto").save()
        Currency(name="Dash",     code="DASH", currency_type="Crypto").save()
        Currency(name="Ripple",   code="XRP",  currency_type="Crypto").save()

    def _banks(self):
        venezuela = Country.objects.get(name="Venezuela")
        usa = Country.objects.get(name="Estados Unidos")
        Bank(swift="MER123", country=venezuela, name="Banco Mercantil").save()
        Bank(swift="BAN123", country=venezuela, name="Banesco Banco Universal").save()

        Bank(swift="WELL123", country=usa, name="Wells Fargo").save()
        Bank(swift="BOA123",  country=usa, name="Bank of America").save()
        Bank(swift="CHAS123", country=usa, name="Chanse Bank").save()



    def handle(self, *args, **options):
        self._permissions()
        self._countries()
        self._banks()
        self._currencies()
        GlobalSettings().save()
        User.objects.create_superuser("admin@admin.com", 'admin')



    
    
    
