from django import forms
from django.contrib.auth.forms import UserCreationForm
from app.models import User
from django.contrib.auth.forms import PasswordChangeForm
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


class PasswordChangeCustomForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super(PasswordChangeCustomForm, self).__init__(user,*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'