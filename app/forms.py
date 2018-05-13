from django import forms
from django.contrib.auth.forms import UserCreationForm
from app.models import *
from django.utils.translation import ugettext as _
from app.customWidgets import *
class SignUpForm(UserCreationForm):

  first_name = forms.CharField(max_length=30, required=True, label='Nombre')
  last_name = forms.CharField(max_length=30, required=True, label='Apellido')
  mobile_phone = forms.RegexField(regex=r'^\+?1?\d{9,15}$', required=True, label="Número móvil ( +542125834456 )")
                                

  def __init__(self, *args, **kwargs):
    super(SignUpForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})
  
  def save(self, *args, **kwargs):
    self.email = self.email.lower() # Quitar mayusculas
    self.first_name = self.first_name.title() # Capitalizar
    self.last_name = self.last_name.title() # Capitalizar
    return super(User, self).save(*args, **kwargs)

  class Meta:
    model = User
    fields = ('first_name', 'last_name', 'mobile_phone', 'email', 'password1', 'password2', )


class AuthenticationForm(forms.Form):

  email = forms.EmailField(required=True, label=_(u"Email"))
  password1 = forms.CharField(widget=forms.PasswordInput, required=True, label=_(u"Password"))

  def __init__(self, *args, **kwargs):
    super(AuthenticationForm, self).__init__(*args, **kwargs)
    for i in self.fields:
        self.fields[i].widget.attrs.update({'class' : 'form-control', 'placeholder': self.fields[i].label})
                

class FromAccountForm(forms.Form):
  Bancos = ((0, _("Elige una cuenta")),
            (1, _("xxxx4323 (Wells Fargo, USA)")),
           (2, _("xxxx4323 (Bank of America, USA)")),
           (3, _("xxxx1982 (HSBC, Argnetina)")))


  account = forms.ChoiceField(choices=Bancos,label="Cuenta origen", widget=forms.Select(), required=True)
  def __init__(self, *args, **kwargs):
    super(FromAccountForm, self).__init__(*args, **kwargs)
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})

class BankAccountForm(forms.Form):

  bank = GroupedModelChoiceField(label=_('Banco'), group_by_field='country', queryset=Bank.objects.all())
  account = forms.CharField(required=True, label=_(u"Número de cuenta"))
  owner = forms.CharField(required=True, label=_(u"Nombre del titular"))
  email = forms.EmailField(required=True, label=_(u"Email del titular"))

  def __init__(self, *args, **kwargs):
    super(BankAccountForm, self).__init__(*args, **kwargs)
    self.fields['account'].widget.attrs.update({'class' : 'form-control', 'placeholder':'Ej 1013232012'})
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})



   # widget=NumberInput(attrs={'id': 'form_homework', 'step': "0.01"}))

class ToAccountForm(forms.Form):
  Bancos = ((0, _("Elige una cuenta")),
            (1, _("xxxx4323 (Banco Mercantil)")),
           (2, _("xxxx4323 (Banesco)")),
           (3, _("xxxx1982 (Banco de Venezuela)")))


  account = forms.ChoiceField(choices=Bancos,label="Cuenta destino", widget=forms.Select(), required=True)
  amount = forms.FloatField(required=True, label="Monto")

  def __init__(self, *args, **kwargs):
    super(ToAccountForm, self).__init__(*args, **kwargs)
    for i in self.fields:
      self.fields[i].widget.attrs.update({'class' : 'form-control'})
