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
  id_number = forms.CharField(max_length=30, required=True, label='Número de identificación')

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

  def __init__(self, *args, **kwargs):
    super(ChangeEmailForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})

class AuthenticationForm(forms.Form):

  email = forms.EmailField(required=True, label=_(u"Email"))
  password1 = forms.CharField(widget=forms.PasswordInput, required=True, label=_(u"Password"))

  def __init__(self, *args, **kwargs):
    super(AuthenticationForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})
                

class BankAccountForm(forms.Form):
  bank = GroupedModelChoiceField(label=_('Banco*'), group_by_field='country', queryset=None)
  number = forms.CharField(required=True, label=_(u"Número de cuenta*"))
  router = forms.CharField(required=False, label=_(u"Número ABA (Solo para bancos en EEUU)"))
  id_currency = forms.ModelChoiceField(label=_('Moneda*'), required=True, queryset=Currency.objects.filter(currency_type='FIAT'))

  def __init__(self, canBuyDollar = False, *args, **kwargs):
    super(BankAccountForm, self).__init__(*args, **kwargs)
    if canBuyDollar:
      self.fields['bank'].queryset = Bank.objects.all()
    else:
      self.fields['bank'].queryset = Bank.objects.all().exclude(country="Venezuela")
    # self.fields['account'].widget.attrs.update({'class' : 'form-control', 'placeholder':'Ej 1013232012'})
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})


class BankAccountDestForm(BankAccountForm):
  bank = ModelChoiceField(label=_('Banco*'), required=True, queryset=Bank.objects.all())
  owner = forms.CharField(required=True, label=_(u"Nombre del titular*"))
  id_number = forms.CharField(max_length=30, required=True, label=_(u'Número de identificación*'))
  email = forms.EmailField(required=True, label=_(u"Email del titular*"))
  alias = forms.CharField(required=False, label=_(u"Alias"))


class FromAccountForm(forms.Form):
  account = forms.ModelChoiceField(queryset=None,label="Cuenta origen", required=True)
  currency = forms.ModelChoiceField(label=_('Moneda'), required=True, queryset=Currency.objects.filter(currency_type='FIAT'))

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
  account = forms.ModelChoiceField(queryset=None, label="Cuenta destino", required=False )
  amount = forms.FloatField(required=False, label="Monto")

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
                        widget = forms.TextInput(attrs={'style': 'width:100%;', 'placeholder': 'VEF, USD, BTC...'})) # VEF, USD, BTC
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
                        widget = forms.TextInput(attrs={'style': 'width:100%;', 'placeholder': 'VEF, USD, BTC...', 'readonly':'readonly'})) # VEF, USD, BTC
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

  rate = forms.FloatField(required=True, label="Tasa" , min_value=0)
  origin_currency = forms.ModelChoiceField(required=True, label="Moneda origen",
                          widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}), queryset=Currency.objects.all())
  target_currency = forms.ModelChoiceField(required=True, label="Moneda destino",
                                  widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}), queryset=Currency.objects.all())

  def __init__(self,*args,**kwargs):

      super(NewExchangeRateForm,self).__init__(*args,**kwargs)
      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
    
class NewBankForm(forms.Form):

  name = forms.CharField(max_length=100, required=True, label="Nombre", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  country = forms.ModelChoiceField(required=True, label="País", widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}), queryset=Country.objects.all())
  swift = forms.CharField(max_length=12, required=True, label="SWIFT", widget = forms.TextInput(attrs={'style': 'width:100%;'}))

  def __init__(self, *args, **kwargs):
    super(NewBankForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

class EditBankForm(forms.ModelForm):

  name = forms.CharField(max_length=100, required=True, label="Nombre", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  country = forms.ModelChoiceField(required=True, label="País", widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}), queryset=Country.objects.all())
  swift = forms.CharField(max_length=12, required=True, label="SWIFT", widget = forms.TextInput(attrs={'style': 'width:100%;', 'readonly':'readonly'}))

  def __init__(self, *args, **kwargs):

    super(EditBankForm, self).__init__(*args, **kwargs)
    if 'instance' in kwargs:
      allies = User.objects.filter(groups__name='Aliado-1').filter(hasAccount__id_account__id_bank__swift=kwargs['instance'].swift, hasAccount__use_type='Origen')
      self.fields['allies'].queryset = allies
    else:
      self.fields['allies'].queryset = User.objects.none()
    self.fields['allies'].label = 'Aliados'
    self.fields['allies'].required = False
    self.fields['acceptBanks'].choices =  format(queryset=Bank.objects.exclude(swift=kwargs['instance'].swift), field='country') 

    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
  class Meta:
    model = Bank
    fields = ('name', 'country', 'swift', 'allies', 'acceptBanks' )

def format(queryset, field):
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

class NewAccountForm(forms.Form):

    number = forms.CharField(max_length=270, required=True, label="Número de cuenta", widget = forms.TextInput(attrs={'style': 'width:100%;'}))  
    choices_third = (('Cliente', 'Cliente'), ('Aliado', 'Aliado'), ('Terceros', 'Terceros'))
    is_thirds = forms.ChoiceField(choices=choices_third, required=True, label="Dueño de la cuenta",
                                    widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))
    choices_use = (('Origen', 'Origen'), ('Destino', 'Destino'))
    use_type = forms.ChoiceField(choices=choices_use, required=True, label="Tipo de uso",
                                    widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))
    bank = GroupedModelChoiceField(label=_('Banco'), group_by_field='country', queryset=Bank.objects.all())
    aba = forms.CharField(max_length=10, required=True, label="ABA", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
    currency = forms.ModelChoiceField(required=True, label="Moneda", queryset=Currency.objects.all(),
                                    widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))

    # Client owner case
    client = forms.MultipleChoiceField(choices=format(queryset=User.objects.filter(groups__name='Cliente'), field='country'), required=False)
    # Aliado owner case
    allie = forms.MultipleChoiceField(choices=format(queryset=User.objects.filter(groups__name__in= ['Aliado-1', 'Aliado-2', 'Aliado-3']), field='country'), required=False)

    #Third one owner case
    owner = forms.CharField(max_length=64, required=False, label="Titular de la cuenta", widget = forms.TextInput(attrs={'style': 'width:100%;'}))  
    alias = forms.CharField(max_length=32, required=False, label="Alias", widget = forms.TextInput(attrs={'style': 'width:100%;'}))  
    email = forms.EmailField(required=False, label="E-mail del titular")
    id_number = forms.IntegerField(required=False, label="Número de identificación del titular")
    sub_owners = forms.MultipleChoiceField(choices=format(queryset=User.objects.all(), field='country'))

    def __init__(self,*args,**kwargs):

      super(NewAccountForm,self).__init__(*args,**kwargs)

      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

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
  status_choices = (('0', 'Inactivo',), ('1', 'Activo'))
  status = forms.ChoiceField(required = True,
                    widget=forms.RadioSelect(attrs={'style': 'width:100%; background-color:white'}), 
                    label = "Estado",
                    choices=status_choices)

  def __init__(self, *args, **kwargs):
      super(NewCountryForm, self).__init__(*args, **kwargs)

      self.fields['name'].widget.attrs.update({'class' : 'form-control'})
      self.fields['status'].widget.attrs.update({'class' : 'flat'})


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
  # user_choices = (('Cliente', 'Cliente'), ('Aliado-1', 'Aliado-1'), ('Aliado-2', 'Aliado-2'), ('Aliado-3', 'Aliado-3'), ('Operador', 'Operador'), ('Admin', 'Admin'))
  # user_type = forms.ChoiceField(choices=user_choices, required=True, label="Tipo de usuario")
  referred_by = forms.ModelChoiceField(queryset=None, label='Referido por', required=False, empty_label="Ninguno")
  choices_buy = ((True, 'Si'), (False, 'No'))
  canBuyDollar = forms.ChoiceField(choices=choices_buy, label='¿Puede comprar dólares?', required=True, 
                                    widget=forms.RadioSelect(attrs={'style': 'width:100%; background-color:white'}))

  def __init__(self, *args, **kwargs):
    alliesChoices = kwargs.pop('alliesC') 
    super(NewUserForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})
        self.fields['canBuyDollar'].widget.attrs.update({'class' : 'flat'})


    self.fields['referred_by'].queryset = alliesChoices
    self.fields['coordinatesUsers'].queryset = alliesChoices
    self.fields['coordinatesUsers'].required = False
  def clean_email(self):
    return self.cleaned_data['email'].lower()
  
  def clean_first_name(self):
    return self.cleaned_data['first_name'].title()
  
  def clean_last_name(self):
    return self.cleaned_data['last_name'].title()

  class Meta:
    model = User
    fields = ('first_name', 'last_name', 'email', 'id_number', 'country', 'address', 'mobile_phone', 'referred_by', 'coordinatesUsers', 'canBuyDollar', 'is_superuser', 'groups' )


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
    self.fields['permissions'].choices = format(queryset=Permission.objects.all(), field='content_type')
  class Meta:
    model = Group
    fields = '__all__'