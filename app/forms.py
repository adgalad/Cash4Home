from django import forms
from django.contrib.auth.forms import UserCreationForm
from app.models import User
from django.utils.translation import ugettext as _

print(_('Name'),_('Email'))
class SignUpForm(UserCreationForm):
  first_name = forms.CharField(max_length=30, required=True, label='Nombre')
  last_name = forms.CharField(max_length=30, required=True, label='Apellido')
  
  def __init__(self, *args, **kwargs):
    super(SignUpForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})

  class Meta:
    model = User
    fields = ('first_name', 'last_name', 'email', 'password1', 'password2', )


class AuthenticationForm(forms.Form):

  email = forms.EmailField(required=True, label=_(u"Email"))
  password1 = forms.CharField(widget=forms.PasswordInput, required=True, label=_(u"Password"))

  def __init__(self, *args, **kwargs):
    super(AuthenticationForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})
                

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
    country = forms.CharField(max_length=70, required=True, label="País", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
    swift = forms.CharField(max_length=12, required=True, label="SWIFT", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
    aba = forms.CharField(max_length=10, required=True, label="ABA", widget = forms.TextInput(attrs={'style': 'width:100%;'}))


    def __init__(self, *args, **kwargs):
      super(NewBankForm, self).__init__(*args, **kwargs)
      for i in self.fields:
          self.fields[i].widget.attrs.update({'class' : 'form-control'})

class EditBankForm(forms.Form):

    name = forms.CharField(max_length=100, required=True, label="Nombre", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
    country = forms.CharField(max_length=70, required=True, label="País", widget = forms.TextInput(attrs={'style': 'width:100%;'}))
    swift = forms.CharField(max_length=12, required=True, label="SWIFT", widget = forms.TextInput(attrs={'style': 'width:100%;', 'readonly':'readonly'}))
    aba = forms.CharField(max_length=10, required=True, label="ABA", widget = forms.TextInput(attrs={'style': 'width:100%;'}))


    def __init__(self, *args, **kwargs):
      super(EditBankForm, self).__init__(*args, **kwargs)
      for i in self.fields:
          self.fields[i].widget.attrs.update({'class' : 'form-control'})