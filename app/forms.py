import re
import decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from app.models import *
from django.utils.translation import ugettext as _
from app.customWidgets import *
from functools import partial
from django.db.models import Q
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import Permission, Group
from django.utils import timezone



class GlobalSettingsForm(forms.ModelForm):
  
  def __init__(self, *args, **kwargs):
    super(GlobalSettingsForm, self).__init__(*args, **kwargs)
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})

  class Meta:
    model = GlobalSettings
    fields = "__all__"

class MyPasswordResetForm(PasswordResetForm):
  def save(self, domain_override=None,
           subject_template_name='registration/password_reset_subject.txt',
           email_template_name='registration/password_reset_email.html',
           use_https=False, token_generator=default_token_generator,
           from_email=None, request=None, html_email_template_name=None,
           extra_email_context=None):
    opts = {
      'use_https': request.is_secure(),
      'token_generator': token_generator,
      'from_email': from_email,
      'email_template_name': email_template_name,
      'subject_template_name': subject_template_name,
      'request': request,
      'html_email_template_name': html_email_template_name,
      'extra_email_context': extra_email_context,
      'html_email_template_name': 'registration/password_reset_html_email.html',
    }
    super(MyPasswordResetForm, self).save(**opts)


class SignUpForm(UserCreationForm):

  first_name = forms.CharField(max_length=30, required=True, label='Nombre')
  last_name = forms.CharField(max_length=30, required=True, label='Apellido')
  mobile_phone = forms.RegexField(regex=r'^\+?\d{9,15}$', required=True, label="Número de teléfono ( Ej +582125834456 )")
  country = forms.ModelChoiceField(label=_("País de residencia"), required=True, queryset=Country.objects.filter(status=True), empty_label="País de residencia")
  address = forms.CharField(max_length=100, required=True, label='Dirección')
  id_number = forms.CharField(max_length=30, required=True, label='Número de identificación ( Ej 12345678 )')

  def clean_id_number(self):
    id_number = self.cleaned_data['id_number']
    if not re.match(r'^[0-9]+$', id_number):
      raise forms.ValidationError('El número de identificación no puede contener letras o signos de puntuación.')
    return id_number

  def __init__(self, *args, **kwargs):
    super(SignUpForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})

  
  def clean_email(self):
    return self.cleaned_data['email'].lower()
  
  def clean_first_name(self):
    return self.cleaned_data['first_name'].title()
  
  def clean_last_name(self):
    return self.cleaned_data['last_name'].title()

  class Meta:
    model = User
    fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'id_number', 'country', 'address', 'mobile_phone' )

class ChangeEmailForm(forms.Form):
  email = forms.EmailField(label=_("Email"), max_length=254)

  def clean_email(self):
    return self.cleaned_data['email'].lower()

  def __init__(self, *args, **kwargs):
    super(ChangeEmailForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})

class AuthenticationForm(forms.Form):

  email = forms.EmailField(required=True, label=_(u"Email"))
  password1 = forms.CharField(widget=forms.PasswordInput, required=True, label=_(u"Password"))

  def clean_email(self):
    return self.cleaned_data['email'].lower()

  def __init__(self, *args, **kwargs):
    super(AuthenticationForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})
                

class BankAccountForm(forms.Form):
  bank = GroupedModelChoiceField(label=_('Banco*'), group_by_field='country', required=True, queryset=Bank.objects.all())
  number = forms.CharField(required=True, label=_(u"Número de cuenta*"))
  router = forms.CharField(required=False, label=_(u"Número ABA (Routing Number)"))
  id_currency = forms.ModelChoiceField(label=_('Moneda*'), required=True, queryset=Currency.objects.filter(currency_type='FIAT').order_by('code'))

  def __init__(self, *args, **kwargs):
    super(BankAccountForm, self).__init__(*args, **kwargs)
    # self.fields['account'].widget.attrs.update({'class' : 'form-control', 'placeholder':'Ej 1013232012'})
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})

  def clean_number(self):
    if not re.match(r'^\d+$', self.cleaned_data['number']):
      raise forms.ValidationError("El número de cuenta no puede contener letras o caracteres especiales.")
    return self.cleaned_data['number']

class AccountBelongsToForm(forms.Form):
  owner = forms.CharField(required=True, label=_(u"Nombre del titular*"))
  id_number = forms.CharField(max_length=30, required=True, label=_(u'Número de identificación*'))
  email = forms.EmailField(required=True, label=_(u"Email del titular*"))
  alias = forms.CharField(required=False, label=_(u"Alias"))

  def clean_id_number(self):

    id_number = self.cleaned_data['id_number']
    print("AQUIIIII", id_number, bool(re.match(r'^[0-9]+$', id_number)))
    if not re.match(r'^[0-9]+$', id_number):
      raise forms.ValidationError('El número de identificación no puede contener letras o signos de puntuación.')
    return id_number
  
  def __init__(self, *args, **kwargs):
    super(AccountBelongsToForm, self).__init__(*args, **kwargs)
    self.fields['id_number'].widget.attrs.update({'placeholder':'Ej 12345678'})
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})

class BankAccountDestForm(AccountBelongsToForm, BankAccountForm):
  pass

class FromAccountForm(forms.Form):
  account = forms.ModelChoiceField(queryset=None,label="Cuenta origen", required=True)
  currency = forms.ModelChoiceField(label=_('Moneda'), required=True, queryset=Currency.objects.filter(currency_type='FIAT').order_by('code'))

  def __init__(self, *args, **kwargs):
    super(FromAccountForm, self).__init__(*args, **kwargs)
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})

  def setQueryset(self, queryset):
    self.fields['account'].queryset = queryset
    for i in self.fields:
      print(i)
    return self

class ToAccountForm(forms.Form):
  account = forms.ModelChoiceField(queryset=None, label="Cuenta destino", required=False)
  amount = forms.DecimalField(required=False, label="Monto")

  def __init__(self, *args, **kwargs):
    if 'data' in kwargs and 'prefix' in kwargs and kwargs['prefix'] + '-amount' in kwargs['data']:
      kwargs['data'][kwargs['prefix'] + '-amount'] = kwargs['data'][kwargs['prefix'] + '-amount'].replace(',','')
    super(ToAccountForm, self).__init__(*args, **kwargs)
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})
  
  def setQueryset(self, queryset):
    self.fields['account'].queryset = queryset
    return self


class NewCurrencyForm(forms.Form):

  code = forms.CharField(max_length=10, required=True, label="Código", 
                        widget = forms.TextInput(attrs={'style': 'width:100%;', 'placeholder': 'VES, USD, BTC...'})) # VES, USD, BTC
  name = forms.CharField(max_length=50, required=True, label="Nombre",
                          widget = forms.TextInput(attrs={'style': 'width:100%;', 'placeholder': 'Bolívar, Dólar, Bitcoin...'}))
  choices = (('FIAT', 'FIAT'), ('Crypto', 'Crypto'))
  currency_type = forms.ChoiceField(required=True, choices=choices, label="Tipo de moneda",
                                  widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))

  def __init__(self, *args, **kwargs):
    super(NewCurrencyForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class EditCurrencyForm(forms.Form):

  code = forms.CharField(max_length=10, required=True, label="Código", 
                        widget = forms.TextInput(attrs={'style': 'width:100%;', 'placeholder': 'VES, USD, BTC...', 'readonly':'readonly'})) # VES, USD, BTC
  name = forms.CharField(max_length=50, required=True, label="Nombre",
                          widget = forms.TextInput(attrs={'style': 'width:100%;', 'placeholder': 'Bolívar, Dólar, Bitcoin...'}))
  choices = (('FIAT', 'FIAT'), ('Crypto', 'Crypto'))
  currency_type = forms.ChoiceField(required=True, choices=choices, label="Tipo de moneda",
                                  widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))

  def __init__(self, *args, **kwargs):
    super(EditCurrencyForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class NewExchangeRateForm(forms.Form):

  rate = forms.DecimalField(required=True, label="Tasa" , min_value=0)
  origin_currency = GroupedModelChoiceField(required=True, label="Moneda origen", group_by_field="currency_type",
                          widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}), queryset=Currency.objects.all().order_by('currency_type'))
  target_currency = GroupedModelChoiceField(required=True, label="Moneda destino", group_by_field="currency_type",
                                  widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}), queryset=Currency.objects.all().order_by('currency_type'))

  def __init__(self,*args,**kwargs):

      super(NewExchangeRateForm,self).__init__(*args,**kwargs)
      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
    
class NewBankForm(forms.Form):

  name = forms.CharField(max_length=100, required=True, label="Nombre", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  country = forms.ModelChoiceField(required=True, label="País", widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}), queryset=Country.objects.all())
  swift = forms.CharField(max_length=12, required=True, label="SWIFT", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  can_send = forms.ModelMultipleChoiceField(queryset=Bank.objects.all(), label='Bancos a los que puede transferir', required=False)

  def __init__(self, *args, **kwargs):
    super(NewBankForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class EditBankForm(forms.ModelForm):

  name = forms.CharField(max_length=100, required=True, label="Nombre", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  country = forms.ModelChoiceField(required=True, label="País", widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}), queryset=Country.objects.all())
  swift = forms.CharField(max_length=12, required=True, label="SWIFT", widget = forms.TextInput(attrs={'style': 'width:100%;', 'readonly':'readonly'}))
  can_send = forms.ModelMultipleChoiceField(queryset=Bank.objects.all(), label='Bancos a los que puede transferir', required=False)
  # allies = forms.ModelMultipleChoiceField(queryset=None, required=False, label="Aliados")

  def __init__(self, *args, **kwargs):

    super(EditBankForm, self).__init__(*args, **kwargs)
    if 'instance' in kwargs:
      allies = User.objects.filter(groups__name='Aliado-1').filter(hasAccount__id_account__id_bank__swift=kwargs['instance'].swift, hasAccount__use_type='Origen')
      self.fields['allies'].queryset = allies
    else:
      self.fields['allies'].queryset = User.objects.none()
    self.fields['allies'].label = 'Aliados'
    self.fields['allies'].required = False

    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
  class Meta:
    model = Bank
    fields = ('name', 'country', 'swift', 'allies')

def format(queryset, field=None):
  dictionary = {}
  for i in queryset:
    if hasattr(i, field):
      _field = getattr(i, field)
      if not _field in dictionary: dictionary[_field] = []
      dictionary[_field].append((i.pk,str(i)))

  result = []
  for k in dictionary:
    result.append((k, dictionary[k]))
    
  return sorted(result, key=lambda tup: str(tup[0]))

class NewAccountForm(forms.ModelForm):

    number = forms.CharField(max_length=270, required=True, label="Número de cuenta*", widget = forms.TextInput(attrs={'style': 'width:100%;'}))  
    id_bank = GroupedModelChoiceField(label='Banco*', group_by_field='country', queryset=Bank.objects.all())
    aba = forms.CharField(max_length=10, required=False, label="ABA (Solo para bancos de USA)", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
    id_currency = forms.ModelChoiceField(required=True, label="Moneda*", 
                                    queryset=Currency.objects.filter(currency_type='FIAT').order_by('code'),
                                    widget = forms.Select(attrs={'style': 'width:100%; background-color:white'})
                                  )

    def __init__(self,*args,**kwargs):

      super(NewAccountForm,self).__init__(*args,**kwargs)

      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

    class Meta:
      model = Account
      fields = ('number', 'id_bank', 'aba', 'id_currency')

class NewHolidayForm(forms.Form):
  DateInput = partial(forms.DateInput, {'class': 'datetimepicker'})

  date = forms.DateField(label = "Fecha", required = True, widget = DateInput(), input_formats = ['%d/%m/%Y'])
  description = forms.CharField(label="Descripción", required=True, max_length=140,
                                    widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  country = forms.ModelChoiceField(label="País", required=True, widget = forms.Select(attrs={'style': 'width:100%;'}), queryset=Country.objects.all())

  def __init__(self, *args, **kwargs):
      
      super(NewHolidayForm, self).__init__(*args, **kwargs)
      for i in self.fields:
          self.fields[i].widget.attrs.update({'class' : 'form-control'})

class NewCountryForm(forms.Form):

  name = forms.CharField(label="Nombre", required=True, max_length=70, widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  iso_code = forms.CharField(label="Código Iso", required=True, max_length=6, widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  status_choices = (('0', 'Inactivo',), ('1', 'Activo'))
  status = forms.ChoiceField(required = True,
                    widget=forms.RadioSelect(attrs={'style': 'width:100%; background-color:white'}), 
                    label = "Estado",
                    choices=status_choices)

  def __init__(self, *args, **kwargs):
      super(NewCountryForm, self).__init__(*args, **kwargs)
      self.fields['name'].widget.attrs.update({'class' : 'form-control'})
      self.fields['iso_code'].widget.attrs.update({'class' : 'form-control'})
      self.fields['status'].widget.attrs.update({'class' : 'flat'})

  class Meta:
    model = Country
    fields = "__all__"


class PermissionsModelMultipleChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s" % obj.name


class NewUserForm(forms.ModelForm):

  first_name = forms.CharField(max_length=30, required=True, label='Nombre')
  last_name = forms.CharField(max_length=30, required=True, label='Apellido')
  id_number = forms.CharField(max_length=30, required=True, label='Número de identificación')
  email = forms.EmailField(required=True, label=_(u"Email"))  
  mobile_phone = forms.RegexField(regex=r'^\+?1?\d{9,15}$', required=True, label="Número de teléfono ( Ej +582125834456 )")
  country = forms.ModelChoiceField(label=_("País de residencia"), required=True, queryset=Country.objects.filter(status=True), empty_label="País")
  address = forms.CharField(max_length=100, required=True, label='Dirección')
  referred_by = forms.ModelChoiceField(queryset=User.objects.filter(groups__name__in=['Aliado-1', 'Aliado-2', 'Aliado-3']), 
                                          label='Referido por', required=False, empty_label="Ninguno")
  choices_buy = ((True, 'Si'), (False, 'No'))
  canBuyDollar = forms.ChoiceField(choices=choices_buy, label='¿Puede comprar dólares?', required=True, 
                                    widget=forms.RadioSelect(attrs={'style': 'width:100%; background-color:white'}))

  def __init__(self, *args, **kwargs):

    super(NewUserForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
        self.fields['canBuyDollar'].widget.attrs.update({'class' : 'flat'})

  def clean_email(self):
    return self.cleaned_data['email'].lower()
  
  def clean_first_name(self):
    return self.cleaned_data['first_name'].title()
  
  def clean_last_name(self):
    return self.cleaned_data['last_name'].title()

  def clean_id_number(self):
    id_number = self.cleaned_data['id_number']
    if not re.match(r'^[0-9]+$', id_number):
      raise forms.ValidationError('El número de identificación no puede contener letras o signos de puntuación.')
    return id_number

  class Meta:
    model = User
    fields = ('first_name', 'last_name', 'email', 'id_number', 'country', 'address', 'mobile_phone', 'referred_by', 'coordinatesUsers', 'canBuyDollar', 'is_active', 'groups' )

class NewOwnAccountAssociatedForm(forms.Form):

  account = forms.ModelChoiceField(label="Número de cuenta", queryset=Account.objects.all(), required=True, empty_label="---")
  choices = (('Origen', 'Origen'), ('Destino', 'Destino'))
  use_type = forms.ChoiceField(choices=choices, required=True, label="Tipo de uso")

  def __init__(self, *args, **kwargs):

    super(NewOwnAccountAssociatedForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})


class NewThirdAccountAssociatedForm(forms.Form):

  account = forms.ModelChoiceField(label="Número de cuenta", queryset=Account.objects.all(), required=True, empty_label="---")
  owner = forms.CharField(max_length=64, required=True, label="Titular de la cuenta")
  alias = forms.CharField(max_length=32, required=False, label="Alias")
  email = forms.EmailField(label="Email", required=True)
  id_number = forms.CharField(label='N° de identificación del titular', required=True, max_length=70)

  def clean_id_number(self):
    id_number = self.cleaned_data['id_number']
    if not re.match(r'^[0-9]+$', id_number):
      raise forms.ValidationError('El número de identificación no puede contener letras o signos de puntuación.')
    return id_number

  def __init__(self, *args, **kwargs):

    super(NewThirdAccountAssociatedForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class NewExchangerForm(forms.Form):
    name = forms.CharField(required=True, label="Nombre", max_length=140)
    currency = forms.ModelMultipleChoiceField(required=True, label="Monedas que acepta", queryset=Currency.objects.all())

    def __init__(self, *args, **kwargs):

      super(NewExchangerForm, self).__init__(*args, **kwargs)
      for i in self.fields:
          self.fields[i].widget.attrs.update({'class' : 'form-control'})    

class EditExchangerForm(forms.Form):
    name = forms.CharField(max_length=140, required=True, label="Nombre", widget = forms.TextInput(attrs={'style': 'width:100%;', 'readonly':'readonly'}))
    currency = forms.CharField(max_length=50, required=True, label="Moneda", widget = forms.TextInput(attrs={'style': 'width:100%;', 'readonly':'readonly'}))
    status_choices = ((False, 'Inactivo',), (True, 'Activo'))
    is_active = forms.ChoiceField(required = True,
                    widget=forms.RadioSelect(attrs={'style': 'width:100%; background-color:white'}), 
                    label = "Estado",
                    choices=status_choices)
    amount = forms.DecimalField(label="Cantidad acumulada", required=True)

    def __init__(self, *args, **kwargs):

        super(EditExchangerForm, self).__init__(*args, **kwargs)
        for i in self.fields:
            self.fields[i].widget.attrs.update({'class' : 'form-control'})
        self.fields['is_active'].widget.attrs.update({'class' : 'flat'})

class ChangeOperationStatusForm(forms.Form):
  status_choices = (('Faltan recaudos', 'Faltan recaudos'),
                    ('Por verificar', 'Por verificar'),
                    ('Verificado', 'Verificado'),
                    ('Publicado', 'Publicado'),
                    ('Fondos ubicados', 'Fondos ubicados'),
                    ('Fondos transferidos', 'Fondos transferidos'))
  status = forms.ChoiceField(required=True, choices=status_choices, label="Status de la operación")
  crypto_used = GroupedModelChoiceField(required=False, label="Criptomoneda utilizada", 
                                        queryset=ExchangerAccepts.objects.filter(currency__currency_type='Crypto'),
                                        group_by_field='exchanger')
  rate = forms.DecimalField(required=False, label="Tasa de cambio" , min_value=0)

  def clean_crypto_used(self):
    crypto = self.cleaned_data['crypto_used']
    if self.cleaned_data['status'] == "Fondos ubicados" and crypto is None:
      raise forms.ValidationError('Debe introducir una criptomoneda.')
    return crypto

  def clean_rate(self):
    rate = self.cleaned_data['rate']
    if self.cleaned_data['status'] == "Fondos ubicados" and rate is None:
      raise forms.ValidationError('Debe introducir una criptomoneda.')
    return rate


  def __init__(self, *args, **kwargs):
    super(ChangeOperationStatusForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class PermissionForm(forms.ModelForm):

  def __init__(self, *args, **kwargs):
    super(PermissionForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
  class Meta:
    model = Permission
    fields = '__all__'

class GroupForm(forms.ModelForm):

  def __init__(self, *args, **kwargs):
    super(GroupForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
    self.fields['permissions'].queryset = Permission.objects.all()
  class Meta:
    model = Group
    fields = '__all__'


class TransactionForm(forms.ModelForm):
  currency = GroupedModelChoiceField(required=True, label="Moneda", group_by_field='currency_type',
                                    queryset=Currency.objects.all().order_by('currency_type', 'code'),
                                    widget = forms.Select(attrs={'style': 'width:100%; background-color:white'})
                                  )
  DateInput = partial(forms.DateInput, {'class': 'datetimepicker'})
  transfer_image = forms.FileField(label="Imagen del comprobante", required=False)
  date = forms.DateField(label = "Fecha", required = False, widget = DateInput(), input_formats = ['%d/%m/%Y'])
  amount = forms.CharField(required=True, label="Monto")
  crypto_used = GroupedModelChoiceField(required=True, label="Criptomoneda utilizada", 
                                            queryset=ExchangerAccepts.objects.filter(currency__currency_type='Crypto').order_by('exchanger'),
                                                 group_by_field='exchanger')
  rate = forms.DecimalField(required=True, label="Tasa de cambio" , min_value=0)

  def __init__(self, *args, **kwargs):
    super(TransactionForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
    choices = (('TD', 'Destino'), ('TC', 'Cierre'))
    self.fields['operation_type'].choices = choices

  def clean_amount(self):
    x = float(self.cleaned_data['amount'].replace(',',''))
    if type(x) != float:
      raise forms.ValidationError('Introduzca un número.')
    return decimal.Decimal(x)

  class Meta:
    model = Transaction
    fields = ('operation_type', 'origin_account', 'target_account',
              'to_exchanger', 'currency','transfer_number', 'amount', 'date', 'transfer_image')

class EditOperationForm(forms.ModelForm):

  def __init__(self, *args, **kwargs):
    super(EditOperationForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

  class Meta:
    model = Operation
    fields = ('id_allie_origin', 'account_allie_origin', 'id_allie_target', 'account_allie_target')



class NewRepurchaseOpForm(forms.Form):
  selected = forms.BooleanField(label="Seleccionar", required=False)
  operation = forms.CharField(label="Código de la Operación", required=False)
  amount = forms.DecimalField(required=False, label="Monto", min_value=0)
  DateInput = partial(forms.DateInput, {'class': 'datetimepicker'})
  date = forms.DateField(label = "Fecha", required = False, widget = DateInput(), input_formats = ['%d/%m/%Y'])
  bank = forms.CharField(label="Banco asociado", required=False)
  payback = forms.BooleanField(label="Devuelto", required=False)

  def __init__(self, *args, **kwargs):
    super(NewRepurchaseOpForm, self).__init__(*args, **kwargs)
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})
    self.fields['operation'].widget.attrs.update({'readonly': 'readonly'})
    self.fields['amount'].widget.attrs.update({'readonly': 'readonly'})
    self.fields['date'].widget.attrs.update({'readonly': 'readonly'})
    self.fields['bank'].widget.attrs.update({'readonly': 'readonly'})
    self.fields['payback'].widget.attrs.update({'readonly': 'readonly'})
    self.fields['selected'].widget.attrs.update({'class' : 'flat'})

class NewRepurchaseForm(forms.Form):
    DateInput = partial(forms.DateInput, {'class': 'datetimepicker'})

    date = forms.DateField(label = "Fecha", required = True, widget = DateInput(), input_formats = ['%d/%m/%Y'])
    rate = forms.DecimalField(required=True, label="Tasa de cambio" , min_value=0)
    currency = GroupedModelChoiceField(queryset=ExchangerAccepts.objects.filter(currency__currency_type='Crypto'),
                                               group_by_field='exchanger', required=True, label="Criptomoneda comprada")
    def __init__(self, *args, **kwargs):
      super(NewRepurchaseForm, self).__init__(*args, **kwargs)
      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class SelectCurrencyForm(forms.Form):

    currency = forms.ChoiceField(required=True, label="Moneda origen")

    def __init__(self, *args, **kwargs):
      currenciesC = kwargs.pop('currenciesC')

      super(SelectCurrencyForm, self).__init__(*args, **kwargs)
      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
        
      self.fields['currency'].choices = currenciesC

class FilterDashboardByMonthForm(forms.Form):
    dateMY = forms.CharField(label = "Filtrar por mes", required = False, widget = MonthYearWidget(attrs={"class": "select", "style":"width:50%; display:inline;"}))
    # endedDate = forms.DateField(label = "Filtrar por fecha", required = False, widget = DateInput(), input_formats = ['%d/%m/%Y'])
    def __init__(self, *args, **kwargs):
      super(FilterDashboardByMonthForm, self).__init__(*args, **kwargs)
      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class FilterDashboardByDateForm(forms.Form):
    DateInput = partial(forms.DateInput, {'class': 'datetimepicker'})
    date = forms.DateField(label = "Filtrar por fecha", required = False, widget = DateInput(), input_formats = ['%d/%m/%Y'])
    def __init__(self, *args, **kwargs):
      super(FilterDashboardByDateForm, self).__init__(*args, **kwargs)
      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class FilterDashboardByRangeForm(forms.Form):
    DateInput = partial(forms.DateInput, {'class': 'datetimepicker'})
    start = forms.DateField(label = "Filtrar por rango", required = False, widget = DateInput(), input_formats = ['%d/%m/%Y'])
    end = forms.DateField(label = "Fecha final", required = False, widget = DateInput(), input_formats = ['%d/%m/%Y'])
   
    def __init__(self, *args, **kwargs):
      super(FilterDashboardByRangeForm, self).__init__(*args, **kwargs)
      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class OperationBulkForm(forms.Form):
    selected = forms.BooleanField(label="Seleccionar", required=False)
    operation = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
      super(OperationBulkForm, self).__init__(*args, **kwargs)
      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
      self.fields['operation'].widget.attrs.update({'readonly': 'readonly'})
      self.fields['selected'].widget.attrs.update({'class' : 'flat'})

class StateChangeBulkForm(forms.Form):
    choices = (('Verificado', 'Verificado'), ('Publicado', 'Publicado'))
    action = forms.ChoiceField(choices=choices, required=False)
    #crypto_used = GroupedModelChoiceField(required=False, label="Criptomoneda utilizada", 
    #                                        queryset=ExchangerAccepts.objects.filter(currency__currency_type='Crypto').order_by('exchanger'),
    #                                             group_by_field='exchanger')
    #rate = forms.DecimalField(required=False, label="Tasa de cambio" , min_value=0)

    def __init__(self, *args, **kwargs):
      super(StateChangeBulkForm, self).__init__(*args, **kwargs)
      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control2'})

class ClosureTransactionForm(forms.Form):
    exchanger = GroupedModelChoiceField(required=False, label="Moneda", 
                                            queryset=ExchangerAccepts.objects.all().order_by('exchanger'),
                                                 group_by_field='exchanger')
    DateInput = partial(forms.DateInput, {'class': 'datetimepicker'})
    date2 = forms.DateField(label = "Fecha", required = False, widget = DateInput(), input_formats = ['%d/%m/%Y'])
    amount = amount = forms.CharField(required=True, label="Monto total")
    transfer_image = forms.FileField(label="Imagen del comprobante", required=False)
    choices = (('O', 'Origen'), ('D', 'Destino'))
    type_account = forms.ChoiceField(choices=choices, required=False, label="¿Aliado origen o destino?")
    transfer_number = forms.CharField(required=False, label="Número de la transferencia")

    def clean_amount(self):
      x = float(self.cleaned_data['amount'].replace(',',''))
      if type(x) != float:
        raise forms.ValidationError('Introduzca un número.')
      return decimal.Decimal(x)

    def __init__(self, *args, **kwargs):
      super(ClosureTransactionForm, self).__init__(*args, **kwargs)
      for i in self.fields:
          self.fields[i].widget.attrs.update({'class' : 'form-control'})