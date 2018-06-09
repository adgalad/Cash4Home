from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
import os
from django.utils import timezone
import random
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

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)

def get_image_path(instance, filename):
    return os.path.join('photos', str(instance), filename)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True)
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
    country = models.CharField(max_length=70)

    USERNAME_FIELD = 'email'
    objects = MyUserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def get_short_name(self):
        return self.first_name

    @property
    def canVerify(self):
        return not (self.verified or self.id_front or self.selfie_image)


class Holiday(models.Model):
    #The primary key is the django id
    date = models.DateField()
    description = models.CharField(max_length=140)
    country = models.CharField(max_length=70)

class Currency(models.Model):
    code = models.CharField(max_length=10, primary_key=True, unique=True) # VEF, USD, BTC
    name = models.CharField(max_length=50)
    choices = (('FIAT', 'FIAT'), ('Crypto', 'Crypto'))
    currency_type = models.CharField(choices=choices, max_length=7)

    def __str__(self):
        return self.code

class ExchangeRate(models.Model):
    # The primary key is the django id
    rate = models.FloatField()
    date = models.DateTimeField()
    origin_currency = models.ForeignKey(Currency, related_name='origin_currency_pair')
    target_currency = models.ForeignKey(Currency, related_name='target_currency_pair')
    def __str__(self):
        return str(self.origin_currency) + "/" + str(self.target_currency)

class Bank(models.Model):
    swift = models.CharField(max_length=12, primary_key=True, unique=True, blank=True)
    country = models.ForeignKey('Country', related_name='banks')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Account(models.Model):
    number = models.CharField(max_length=270)
    is_client = models.BooleanField()
    choices = (('Origen', 'Origen'), ('Destino', 'Destino'))
    use_type = models.CharField(choices=choices, max_length=8, blank=True)
    id_bank = models.ForeignKey(Bank)
    id_currency = models.ForeignKey(Currency)
    aba = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return str(self.id_bank) + " " + str(self.number)

class AccountBelongsTo(models.Model):
    # The primary key is the django id
    id_account = models.ForeignKey(Account)
    id_client = models.ForeignKey(User)

    owner = models.CharField(max_length=64, null=True)
    alias = models.CharField(max_length=32, null=True)
    email = models.EmailField(null=True)
    id_number = models.IntegerField(verbose_name='ID number', null=True)

    class Meta:
        unique_together = ('id_account', 'id_client')

    def __str__(self):
        name = str(self.id_account)
        if not self.alias is None:
            name = self.alias + " (" + name + ")"
        return name


def pkgenTransaction():
    return "Tx"+str(round(timezone.now().timestamp()))+str(random.randint(0,10000))


class Operation(models.Model):
    code = models.CharField(max_length=100, primary_key=True, unique=True)
    fiat_amount = models.DecimalField(max_digits=30, decimal_places=15)
    crypto_rate = models.FloatField(blank=True, null=True)
    status_choices = (('Falta verificacion', 'Falta verificacion'), ('Por verificar', 'Por verificar'), ('Verificado', 'Verificado'), ('Fondos por ubicar', 'Fondos por ubicar'),
                      ('Fondos ubicados', 'Fondos ubicados'), ('Fondos transferidos', 'Fondos transferidos'))
    status = models.CharField(choices=status_choices, max_length=20)
    exchanger = models.CharField(max_length=70, blank=True, null=True)
    date = models.DateTimeField()
    id_client = models.ForeignKey(User, related_name="user_client")
    id_account = models.ForeignKey(Account, related_name='account_client_origin') # Origin account from the client
    exchange_rate = models.FloatField()
    origin_currency = models.ForeignKey(Currency, related_name='origin_currency_used')
    target_currency = models.ForeignKey(Currency, related_name='target_currency_used')
    date_ending = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    account_allie_origin = models.ForeignKey(Account, related_name='account_allie_origin')
    id_allie_origin = models.ForeignKey(User, related_name='user_allie_origin')
    account_allie_target = models.ForeignKey(Account, related_name='account_allie_target', blank=True, null=True)
    id_allie_target = models.ForeignKey(User, related_name='user_allie_target', blank=True, null=True)

    def save(self, *args, **kwargs):
        if (self.pk):
            self.is_active = (self.date < self.date_ending)
        super(Operation, self).save(*args, **kwargs)

    def save(self, fromCountry, toCountry, date, *args, **kwargs):
        
        self.code = "MT-%s-%s-%s-%s"%(fromCountry, toCountry, date.strftime("%d%m%Y"), Operation.objects.all().count())
        print(self.code)
        super(Operation, self).save(*args, **kwargs)
        return self.code

class OperationGoesTo(models.Model):
    # The primary key is the django id
    operation_code = models.ForeignKey(Operation)
    number_account = models.ForeignKey(Account)
    amount = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = ('operation_code', 'number_account')

class Transaction(models.Model):
    code = models.CharField(max_length=100, primary_key=True, unique=True, default=pkgenTransaction)
    date = models.DateTimeField()
    choices = (('TO', 'TO'), ('TD', 'TD'), ('TE', 'TE')) #TO-Transaccion origen, TD-Transaccion destino, TC-transaccion crypto
    operation_type = models.CharField(choices=choices, max_length=3)
    transfer_image = models.ImageField(upload_to=get_image_path)
    origin_account = models.ForeignKey(Account, blank=True, null=True, related_name='origin_account')
    target_account = models.ForeignKey(Account, blank=True, null=True, related_name='target_account')

class Repurchase(models.Model):
    # The primary key is the django id
    date = models.DateTimeField()
    rate = models.FloatField()
    origin_currency = models.ForeignKey(Currency, related_name='origin_currency_purchase')
    target_currency = models.ForeignKey(Currency, related_name='target_currency_purchase')

class RepurchaseCameFrom(models.Model):
    # The primary key is the django id
    id_repurchase = models.ForeignKey(Repurchase)
    id_operation = models.ForeignKey(Operation)

    class Meta:
        unique_together = ('id_repurchase', 'id_operation')

class Comission(models.Model):
    # The primary key is the django id
    id_allie = models.ForeignKey(User)
    id_operation = models.ForeignKey(Operation, blank=True, null=True)
    percentage = models.FloatField()
    choices = (('Pagado', 'Pagado'), ('Por pagar', 'Por pagar'), ('Pagado parcialmente', 'Pagado parcialmente'))
    status = models.CharField(choices=choices, max_length=20)
    remaining = models.DecimalField(max_digits=40, decimal_places=40)


class Country(models.Model):
    name = models.CharField(max_length=70, primary_key=True, unique=True)
    status = models.BooleanField(default=True)
    iso_code = models.CharField(max_length=4)
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class CanSendTo(models.Model):
    # The primary key is the django id
    origin_bank = models.ForeignKey(Bank, related_name='origin_bank')
    target_bank = models.ForeignKey(Bank, related_name='target_bank')

    class Meta:
        unique_together = ('origin_bank', 'target_bank')

class OperationStateChange(models.Model):
    # The primary key is the django id
    date = models.DateTimeField()
    user = models.ForeignKey(User)
    status_choices = (('Falta verificacion', 'Falta verificacion'), ('Por verificar', 'Por verificar'), ('Verificado', 'Verificado'), ('Fondos por ubicar', 'Fondos por ubicar'),
                      ('Fondos ubicados', 'Fondos ubicados'), ('Fondos transferidos', 'Fondos transferidos'))
    original_status = models.CharField(choices=status_choices, max_length=20)

class Exchanger(models.Model):
    name = models.CharField(max_length=140, primary_key=True, unique=True)
    is_active = models.BooleanField(default=True)

class ExchangerAccepts(models.Model):
    # The primary key is the django id
    exchanger = models.ForeignKey(Exchanger)
    currency = models.ForeignKey(Currency)
    amount_acc = models.DecimalField(max_digits=30, decimal_places=15)

class BoxClosure(models.Model):
    # The primary key is the django id
    date = models.DateTimeField()
    user = models.ForeignKey(User)
    currency = models.ForeignKey(Currency)
    exchanger = models.ForeignKey(Exchanger)
    final_amount = models.DecimalField(max_digits=30, decimal_places=15)

    class Meta:
        unique_together = ('date', 'exchanger', 'currency')
