from django import forms
from django.contrib.auth.forms import UserCreationForm
from app.models import *
from django.utils.translation import ugettext as _
from app.customWidgets import *

class SignUpForm(UserCreationForm):

  first_name = forms.CharField(max_length=30, required=True, label='Nombre')
  last_name = forms.CharField(max_length=30, required=True, label='Apellido')
  mobile_phone = forms.RegexField(regex=r'^\+?1?\d{9,15}$', required=True, label="Número de teléfono ( Ej +582125834456 )")
  address = forms.CharField(max_length=30, required=True, label='Dirección')
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
    fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'id_number', 'address', 'mobile_phone' )


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
  account = forms.ModelChoiceField(queryset=None, label="Cuenta origen", required=True )

  def __init__(self, *args, **kwargs):
    super(FromAccountForm, self).__init__(*args, **kwargs)
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})

  def setQueryset(self, queryset):
    self.fields['account'].queryset = queryset
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



