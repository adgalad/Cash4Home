from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator

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
    return os.path.join('photos', str(instance.id), filename)

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
    
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    is_superuser = models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')
    verified     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    first_name   = models.CharField(blank=True, max_length=30, verbose_name='first name')
    last_name    = models.CharField(blank=True, max_length=30, verbose_name='last name')
    address      = models.CharField(blank=True, max_length=64, verbose_name='address')
    id_number    = models.IntegerField(blank=True, verbose_name='ID number', default=0)
    mobile_phone = models.CharField(validators=[phone_regex], blank=True, max_length=16, verbose_name='mobile phone')
    id_front     = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    id_back      = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    selfie_image = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    service_image = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    # validation_status =

    USERNAME_FIELD = 'email'
    objects = MyUserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email


class Bank(models.Model):
    country = models.CharField(blank=True, max_length=30, verbose_name='country')
    name = models.CharField(blank=True, max_length=30, verbose_name='bank name')

    def __str__(self):
        return self.name
