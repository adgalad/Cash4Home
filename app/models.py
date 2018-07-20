from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
import os
from django.utils import timezone
import datetime
import random

class GlobalSettings(models.Model):
    OPERATION_TIMEOUT = models.IntegerField(default=90, verbose_name='Expiración de la operación')
    EMAIL_VALIDATION_EXPIRATION = models.IntegerField(default=60*3, verbose_name='Expiración del email de validación')


    def get():
        settings = GlobalSettings.objects.all()
        if not settings:
            settings = GlobalSettings(OPERATION_TIMEOUT = 90,
                                      EMAIL_VALIDATION_EXPIRATION = 60*3
                                    )
            settings.save()
            return settings
        else:
            return settings[0]


class Country(models.Model):
    name = models.CharField(max_length=70, primary_key=True, unique=True)
    status = models.BooleanField(default=True)
    iso_code = models.CharField(max_length=4)
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        default_permissions = ()

    def __str__(self):
        return self.name

class MyUserManager(BaseUserManager):
    """
    A custom user manager to deal with emails as unique identifiers for auth
    instead of usernames. The default that's used is "UserManager"
    """
    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('verified', True)
        extra_fields.setdefault('canBuyDollar', True)
        extra_fields.setdefault('country', Country.objects.all()[0])


        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)

def get_image_path(instance, filename):
    return os.path.join('photos', str(instance), filename)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    
    phone_regex = RegexValidator(regex=r'^\+?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    is_superuser = models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')
    verified     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    first_name   = models.CharField(blank=True, max_length=30, verbose_name='first name')
    last_name    = models.CharField(blank=True, max_length=30, verbose_name='last name')
    address      = models.CharField(blank=True, max_length=64, verbose_name='address')
    id_number    = models.CharField(blank=True, verbose_name='ID number', default=0, max_length=70)
    mobile_phone = models.CharField(validators=[phone_regex], blank=True, max_length=16, verbose_name='mobile phone')
    id_front     = models.ImageField(upload_to=get_image_path, null=True)
    id_back      = models.ImageField(upload_to=get_image_path, null=True)
    selfie_image = models.ImageField(upload_to=get_image_path, null=True)
    service_image = models.ImageField(upload_to=get_image_path, null=True)
    user_choices = (('Cliente', 'Cliente'), ('Aliado-1', 'Aliado-1'), ('Aliado-2', 'Aliado-2'), ('Aliado-3', 'Aliado-3'), ('Operador', 'Operador'), ('Admin', 'Admin'))
    user_type = models.CharField(choices=user_choices, max_length=9, blank=True)
    referred_by = models.ForeignKey('self', null=True, blank=True)
    canBuyDollar = models.BooleanField(default=False)
    country = models.ForeignKey(Country)

    coordinatesUsers = models.ManyToManyField('self', verbose_name='Aliados que coordina', blank=True)

    USERNAME_FIELD = 'email'
    objects = MyUserManager()


    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def get_short_name(self):
        return self.first_name

    @property
    def id_front_url(self):
        if self.id_front and hasattr(self.id_front, 'url'):
            return self.id_front.url
        else:
            return '/static/images/placeholder.png'
    @property
    def selfie_image_url(self):
        if self.selfie_image and hasattr(self.selfie_image, 'url'):
            return self.selfie_image.url
        else:
            return '/static/images/placeholder.png'
    
    @property
    def service_image_url(self):
        if self.service_image and hasattr(self.service_image, 'url'):
            return self.service_image.url
        else:
            return '/static/images/placeholder.png'

    @property
    def id_back_url(self):
        if self.id_back and hasattr(self.id_back, 'url'):
            return self.id_back.url
        else:
            return '/static/images/placeholder.png'

    @property
    def canVerify(self):
        return not (self.verified or self.id_front or self.selfie_image or self.id_back)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


class Holiday(models.Model):
    #The primary key is the django id
    date = models.DateField()
    description = models.CharField(max_length=140)
    country = models.ForeignKey(Country)

    def __str__(self):
        return str(self.date) + ' ' + self.description
    class Meta:
        default_permissions = ()

class Currency(models.Model):
    code = models.CharField(max_length=10, primary_key=True, unique=True) # VEF, USD, BTC
    name = models.CharField(max_length=50)
    choices = (('FIAT', 'FIAT'), ('Crypto', 'Crypto'))
    currency_type = models.CharField(choices=choices, max_length=7)

    def __str__(self):
        return self.code

    class Meta:
        default_permissions = ()

class ExchangeRate(models.Model):
    # The primary key is the django id
    rate = models.DecimalField(max_digits=30, decimal_places=15)
    date = models.DateTimeField(auto_now_add=True)
    origin_currency = models.ForeignKey(Currency, related_name='origin_currency_pair')
    target_currency = models.ForeignKey(Currency, related_name='target_currency_pair')
    
    def __str__(self):
        return str(self.origin_currency) + "/" + str(self.target_currency)

    class Meta:
        default_permissions = ()

class Bank(models.Model):
    swift = models.CharField(max_length=12, primary_key=True, unique=True, blank=True)
    country = models.ForeignKey('Country', related_name='banks')
    name = models.CharField(max_length=100)
    allies = models.ManyToManyField(User, blank=True)
    
    def __str__(self):
        return self.name

    class Meta:
        default_permissions = ()


class Account(models.Model):
    number = models.CharField(max_length=270)
    
    id_bank = models.ForeignKey(Bank)
    id_currency = models.ForeignKey(Currency)
    aba = models.CharField(max_length=10, null=True)

    def __str__(self):
        return str(self.id_bank) + " " + str(self.number[-4:])

    @property
    def full(self):
        return str(self.id_bank) + " " + str(self.number)

    class Meta:
        default_permissions = ()

class AccountBelongsTo(models.Model):
    # The primary key is the django id
    id_account = models.ForeignKey(Account, related_name='belongsTo')
    id_client = models.ForeignKey(User, related_name='hasAccount')
    choices = (('Origen', 'Origen'), ('Destino', 'Destino'))
    use_type = models.CharField(choices=choices, max_length=8, blank=True)
    owner = models.CharField(max_length=64)
    alias = models.CharField(max_length=32, null=True)
    email = models.EmailField(null=True)
    id_number = models.CharField(blank=True, verbose_name='ID number', default=0, max_length=70, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('id_account', 'id_client')
        default_permissions = ()

    def __str__(self):
        name = str(self.id_account)
        if not self.alias is None:
            name = self.alias + " (" + name + ")"
        return name


def pkgenTransaction():
    return "Tx"+str(round(timezone.now().timestamp()))+str(random.randint(0,10000))

class Exchanger(models.Model):
    name = models.CharField(max_length=140, primary_key=True, unique=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        default_permissions = ()

    def __str__(self):
        return self.name

class ExchangerAccepts(models.Model):
    # The primary key is the django id
    exchanger = models.ForeignKey(Exchanger)
    currency = models.ForeignKey(Currency)
    amount_acc = models.DecimalField(max_digits=30, decimal_places=15)
    
    class Meta:
        default_permissions = ()

    def __str__(self):
        return str(self.currency.code)

class Operation(models.Model):
    code = models.CharField(max_length=100, primary_key=True, unique=True)
    fiat_amount = models.DecimalField(max_digits=30, decimal_places=15)
    crypto_rate = models.DecimalField(blank=True, null=True, max_digits=30, decimal_places=15)
    crypto_used = models.ForeignKey(Currency, related_name='crypto_used', blank=True, null=True)
    status_choices = (('Cancelada', 'Cancelada'),
                      ('Falta verificacion', 'Falta verificacion'),
                      ('Por verificar', 'Por verificar'), 
                      ('Verificado', 'Verificado'),
                      ('Fondos por ubicar', 'Fondos por ubicar'),
                      ('Fondos ubicados', 'Fondos ubicados'),
                      ('Fondos transferidos', 'Fondos transferidos'),
                      ('En reclamo', 'En reclamo'))
    status = models.CharField(choices=status_choices, max_length=20)
    exchanger = models.ForeignKey(Exchanger, blank=True, null=True)
    date = models.DateTimeField()
    expiration = models.DateTimeField()
    id_client = models.ForeignKey(User, related_name="user_client")
    id_account = models.ForeignKey(Account, related_name='account_client_origin') # Origin account from the client
    exchange_rate = models.DecimalField(max_digits=30, decimal_places=15)
    origin_currency = models.ForeignKey(Currency, related_name='origin_currency_used')
    target_currency = models.ForeignKey(Currency, related_name='target_currency_used')
    is_active = models.BooleanField(default=True)
    account_allie_origin = models.ForeignKey(Account, related_name='account_allie_origin', verbose_name="Cuenta aliado origen", blank=True, null=True)
    id_allie_origin = models.ForeignKey(User, related_name='user_allie_origin', verbose_name="Aliado origen", blank=True, null=True)
    account_allie_target = models.ForeignKey(Account, related_name='account_allie_target', verbose_name="Cuenta aliado origen", blank=True, null=True)
    id_allie_target = models.ForeignKey(User, related_name='user_allie_target', verbose_name="Aliado destino", blank=True, null=True)

    def save(self, *args, **kwargs):
        if (self.pk and self.is_active):
            self.is_active = (not self.status == 'Falta verificacion') or (timezone.now() < self.expiration)
        super(Operation, self).save(*args, **kwargs)


    def _save(self, fromCountry, toCountry, date, *args, **kwargs):
        
        self.code = "MT-%s-%s-%s-%s"%(fromCountry, toCountry, date.strftime("%d%m%Y"), Operation.objects.all().count())
        self.save(*args, **kwargs)
        return self.code

    def isCanceled(self):
        if self.status == 'Cancelada' or not self.is_active:
            return True
        elif timezone.now() > self.expiration and self.status == 'Falta verificacion':
            self.status = 'Cancelada'
            self.is_active = False
            self.save()
            return True
        return False
    
    def __str__(self):
        return self.code

    class Meta:
        default_permissions = ()

class OperationGoesTo(models.Model):
    # The primary key is the django id
    operation_code = models.ForeignKey(Operation, related_name='goesTo')
    number_account = models.ForeignKey(Account)
    amount = models.DecimalField(blank=True, null=True, max_digits=30, decimal_places=15)

    class Meta:
        unique_together = ('operation_code', 'number_account')
        default_permissions = ()

class Transaction(models.Model):
    code = models.CharField(max_length=100, primary_key=True, unique=True, default=pkgenTransaction)
    date = models.DateField(verbose_name="Fecha")
    choices = (('TO', 'TO'), ('TD', 'TD'), ('TC', 'TC')) #TO-Transaccion origen, TD-Transaccion destino, TC-transaccion crypto
    operation_type = models.CharField(choices=choices, max_length=3, verbose_name="Tipo de transacción")
    transfer_image = models.ImageField(upload_to=get_image_path, verbose_name="Imagen del comprobante")
    id_operation   = models.ForeignKey(Operation, related_name='transactions', verbose_name="Operación asociada")
    origin_account = models.ForeignKey(Account, null=True, blank=True, related_name='origin_account', verbose_name="Cuenta origen")
    target_account = models.ForeignKey(Account, null=True, blank=True, related_name='target_account', verbose_name="Cuenta destino")
    to_exchanger   = models.ForeignKey('Exchanger', null=True, blank=True, verbose_name="Exchanger")
    amount         = models.FloatField(verbose_name="Monto")
    currency       = models.ForeignKey(Currency, verbose_name="Moneda")

    @property
    def image_url(self):
        if self.transfer_image and hasattr(self.transfer_image, 'url'):
            return self.transfer_image.url
        else:
            return '/static/images/placeholder.png'

    class Meta:
        default_permissions = ()

class Repurchase(models.Model):
    # The primary key is the django id
    date = models.DateTimeField()
    rate = models.DecimalField(max_digits=30, decimal_places=15)
    origin_currency = models.ForeignKey(Currency, related_name='origin_currency_purchase')
    target_currency = models.ForeignKey(Currency, related_name='target_currency_purchase')
    exchanger = models.ForeignKey(Exchanger)
    amount = models.DecimalField(max_digits=30, decimal_places=15, default=0)
    profit = models.DecimalField(default=0, max_digits=30, decimal_places=15)

    class Meta:
        default_permissions = ()

class RepurchaseCameFrom(models.Model):
    # The primary key is the django id
    id_repurchase = models.ForeignKey(Repurchase)
    id_operation = models.ForeignKey(Operation)

    class Meta:
        unique_together = ('id_repurchase', 'id_operation')
        default_permissions = ()

class Comission(models.Model):
    # The primary key is the django id
    id_allie = models.ForeignKey(User)
    id_operation = models.ForeignKey(Operation, blank=True, null=True)
    percentage = models.FloatField()
    choices = (('Pagado', 'Pagado'), ('Por pagar', 'Por pagar'), ('Pagado parcialmente', 'Pagado parcialmente'))
    status = models.CharField(choices=choices, max_length=20)
    remaining = models.DecimalField(max_digits=40, decimal_places=40)
    
    class Meta:
        default_permissions = ()

class CanSendTo(models.Model):
    # The primary key is the django id
    origin_bank = models.ForeignKey(Bank, related_name='canSendTo')
    target_bank = models.ForeignKey(Bank, related_name='canReceiveFrom')

    class Meta:
        unique_together = ('origin_bank', 'target_bank')
        default_permissions = ()


class OperationStateChange(models.Model):
    # The primary key is the django id
    date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    status_choices = (('Falta verificacion', 'Falta verificacion'), ('Por verificar', 'Por verificar'), ('Verificado', 'Verificado'), ('Fondos por ubicar', 'Fondos por ubicar'),
                      ('Fondos ubicados', 'Fondos ubicados'), ('Fondos transferidos', 'Fondos transferidos'), ('En reclamo', 'En reclamo'))
    original_status = models.CharField(choices=status_choices, max_length=20)
    new_status = models.CharField(choices=status_choices, max_length=20)
    operation = models.ForeignKey(Operation, null=True, related_name='changeHistory')
    
    class Meta:
        default_permissions = ()

class BoxClosure(models.Model):
    # The primary key is the django id
    date = models.DateTimeField()
    user = models.ForeignKey(User)
    currency = models.ForeignKey(Currency)
    exchanger = models.ForeignKey(Exchanger)
    final_amount = models.DecimalField(max_digits=30, decimal_places=15)

    class Meta:
        unique_together = ('date', 'exchanger', 'currency')
        default_permissions = ()