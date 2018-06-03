from django import forms
from django.contrib.auth.forms import UserCreationForm
from app.models import *
from django.utils.translation import ugettext as _
from app.customWidgets import *
from functools import partial

class SignUpForm(UserCreationForm):

  first_name = forms.CharField(max_length=30, required=True, label='Nombre')
  last_name = forms.CharField(max_length=30, required=True, label='Apellido')
  mobile_phone = forms.RegexField(regex=r'^\+?1?\d{9,15}$', required=True, label="Número de teléfono ( Ej +582125834456 )")
  country = forms.ChoiceField(required=True, label="País de residencia")
  address = forms.CharField(max_length=30, required=True, label='Dirección')
  id_number = forms.CharField(max_length=30, required=True, label='Número de identificación')

  def __init__(self, *args, **kwargs):
    countriesChoices = kwargs.pop('countriesC') 

    super(SignUpForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})

    self.fields['country'].choices = countriesChoices
  
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
  email = forms.EmailField(required=True, label=_(u"Email"))  



class AuthenticationForm(forms.Form):

  email = forms.EmailField(required=True, label=_(u"Email"))
  password1 = forms.CharField(widget=forms.PasswordInput, required=True, label=_(u"Password"))

  def __init__(self, *args, **kwargs):
    super(AuthenticationForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})
                

class BankAccountForm(forms.Form):
  bank = GroupedModelChoiceField(label=_('Banco'), group_by_field='country', queryset=Bank.objects.all())
  number = forms.CharField(required=True, label=_(u"Número de cuenta"))

  def __init__(self, *args, **kwargs):
    super(BankAccountForm, self).__init__(*args, **kwargs)
    # self.fields['account'].widget.attrs.update({'class' : 'form-control', 'placeholder':'Ej 1013232012'})
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})

class BankAccountDestForm(BankAccountForm):
  owner = forms.CharField(required=True, label=_(u"Nombre del titular"))
  id_number = forms.CharField(max_length=30, required=True, label=_(u'Número de identificación'))
  email = forms.EmailField(required=True, label=_(u"Email del titular"))
  alias = forms.CharField(required=False, label=_(u"Alias"))


class FromAccountForm(forms.Form):
  account = forms.ModelChoiceField(queryset=None, label="Cuenta origen", required=True)
  currency = GroupedModelChoiceField(label=_('Moneda'), required=True, group_by_field='currency_type', queryset=Currency.objects.filter(currency_type='FIAT'))

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

  def __init__(self,*args,**kwargs):
      currencyChoices = kwargs.pop('currencyC')  

      super(NewExchangeRateForm,self).__init__(*args,**kwargs)

      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

      # Set choices from argument.
      self.fields['origin_currency'].choices = currencyChoices
      self.fields['target_currency'].choices = currencyChoices

  rate = forms.CharField(max_length=10, required=True, label="Tasa", 
                        widget = forms.TextInput(attrs={'style': 'width:100%;', 'type': "number"}))
  origin_currency = forms.ChoiceField(required=True, label="Moneda origen",
                          widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))
  target_currency = forms.ChoiceField(required=True, label="Moneda destino",
                                  widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))
    
class NewBankForm(forms.Form):

  name = forms.CharField(max_length=100, required=True, label="Nombre", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  country = forms.ChoiceField(required=True, label="País", widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))
  swift = forms.CharField(max_length=12, required=True, label="SWIFT", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  aba = forms.CharField(max_length=10, required=True, label="ABA", widget = forms.TextInput(attrs={'style': 'width:100%;'}))

  def __init__(self, *args, **kwargs):
    countriesChoices = kwargs.pop('countriesC') 

    super(NewBankForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

    self.fields['country'].choices = countriesChoices

class EditBankForm(forms.Form):

  name = forms.CharField(max_length=100, required=True, label="Nombre", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  country = forms.ChoiceField(required=True, label="País", widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))
  swift = forms.CharField(max_length=12, required=True, label="SWIFT", widget = forms.TextInput(attrs={'style': 'width:100%;', 'readonly':'readonly'}))
  aba = forms.CharField(max_length=10, required=True, label="ABA", widget = forms.TextInput(attrs={'style': 'width:100%;'}))


  def __init__(self, *args, **kwargs):
    countriesChoices = kwargs.pop('countriesC')

    super(EditBankForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

    self.fields['country'].choices = countriesChoices

class NewAccountForm(forms.Form):

    def __init__(self,*args,**kwargs):
      currencyChoices = kwargs.pop('currencyC') 

      super(NewAccountForm,self).__init__(*args,**kwargs)

      for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

      # Set choices from argument.
      self.fields['currency'].choices = currencyChoices

    number = forms.CharField(max_length=270, required=True, label="Número de cuenta", widget = forms.TextInput(attrs={'style': 'width:100%;'}))  
    choices_third = (('Cliente', 'Cliente'), ('Aliado', 'Aliado'), ('Terceros', 'Terceros'))
    is_thirds = forms.ChoiceField(choices=choices_third, required=True, label="Dueño de la cuenta",
                                    widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))
    choices_use = (('Origen', 'Origen'), ('Destino', 'Destino'))
    use_type = forms.ChoiceField(choices=choices_use, required=True, label="Tipo de uso",
                                    widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))
    bank = GroupedModelChoiceField(label=_('Banco'), group_by_field='country', queryset=Bank.objects.all())
    currency = forms.ChoiceField(required=True, label="Moneda",
                                    widget = forms.Select(attrs={'style': 'width:100%; background-color:white'}))

    #Third one owner case
    owner = forms.CharField(max_length=64, required=False, label="Titular de la cuenta", widget = forms.TextInput(attrs={'style': 'width:100%;'}))  
    alias = forms.CharField(max_length=32, required=False, label="Alias", widget = forms.TextInput(attrs={'style': 'width:100%;'}))  
    email = forms.EmailField(required=False, label="E-mail del titular")
    id_number = forms.IntegerField(required=False, label="Número de identificación del titular")

class NewHolidayForm(forms.Form):
  DateInput = partial(forms.DateInput, {'class': 'datetimepicker'})

  date = forms.DateField(label = "Fecha", required = True, widget = DateInput(), input_formats = ['%d/%m/%Y'])
  description = forms.CharField(label="Descripción", required=True, max_length=140,
                                    widget = forms.TextInput(attrs={'style': 'width:100%;'}))
  country = forms.ChoiceField(label="País", required=True, widget = forms.Select(attrs={'style': 'width:100%;'}))

  def __init__(self, *args, **kwargs):
      countriesChoices = kwargs.pop('countriesC')
      
      super(NewHolidayForm, self).__init__(*args, **kwargs)
      for i in self.fields:
          self.fields[i].widget.attrs.update({'class' : 'form-control'})

      self.fields['country'].choices = countriesChoices

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


class NewUserForm(forms.Form):

  first_name = forms.CharField(max_length=30, required=True, label='Nombre')
  last_name = forms.CharField(max_length=30, required=True, label='Apellido')
  id_number = forms.CharField(max_length=30, required=True, label='Número de identificación')
  email = forms.EmailField(required=True, label=_(u"Email"))  
  mobile_phone = forms.RegexField(regex=r'^\+?1?\d{9,15}$', required=True, label="Número de teléfono ( Ej +582125834456 )")
  country = forms.ChoiceField(required=True, label="País de residencia")
  address = forms.CharField(max_length=30, required=True, label='Dirección')
  user_choices = (('Cliente', 'Cliente'), ('Aliado-1', 'Aliado-1'), ('Aliado-2', 'Aliado-2'), ('Aliado-3', 'Aliado-3'), ('Operador', 'Operador'), ('Admin', 'Admin'))
  user_type = forms.ChoiceField(choices=user_choices, required=True, label="Tipo de usuario")
  referred_by = forms.ChoiceField(label='Referido por', required=True)
  choices_buy = ((True, 'Si'), (False, 'No'))
  canBuyDollar = forms.ChoiceField(choices=choices_buy, label='¿Puede comprar dólares?', required=True)

  def __init__(self, *args, **kwargs):
    alliesChoices = kwargs.pop('alliesC') 
    countriesChoices = kwargs.pop('countriesC') 

    super(NewUserForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control'})

    self.fields['referred_by'].choices = alliesChoices
    self.fields['country'].choices = countriesChoices
  
  def clean_email(self):
    return self.cleaned_data['email'].lower()
  
  def clean_first_name(self):
    return self.cleaned_data['first_name'].title()
  
  def clean_last_name(self):
    return self.cleaned_data['last_name'].title()