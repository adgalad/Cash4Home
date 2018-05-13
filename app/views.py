from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth import logout as logout_auth
from django.contrib.auth import login as login_auth
from django.contrib import messages
from django.forms import formset_factory
from io import BytesIO
import time
import json
from app.forms import *

def home(request):
  if request.user.is_authenticated():
    return render(request, 'dashboard.html')
  else:
    return render(request, 'index.html')

def company(request):
  return render(request, 'company.html')

def profile(request):
  return render(request, 'dashboard/profile.html')

def createOperation(request):
  if request.method == 'POST':
    form1 = FromAccountForm(request.POST)
    if form.is_valid():
      pass
  else:
    form1 = FromAccountForm(initial={'fromAmount':1.0})
    data = {
      'form-TOTAL_FORMS': '5',
      'form-INITIAL_FORMS': '5',
      'form-MAX_NUM_FORMS': '5',
    }
    toAccountFormSet = formset_factory(ToAccountForm)
    form2 = toAccountFormSet(data)
  rate = { 1: { 2: 0.7, 3:800000, 'name':"USD"},
           2: { 1: 1.6, 3:1000000, 'name':"EUR"},
           3: { 1: 0.00000125, 2:0.000001, 'name':"VEF"}}

  fee = 0.01

  return render(request, 'dashboard/createOperation.html', {'form1': form1, 'form2': form2, "rate":str(json.dumps(rate)), "fee": str(fee)})

def uploadImage(request):
  if request.method == 'POST':
    print(request.FILES)
    
  return render(request, 'dashboard/uploadImage.html')  

def accounts(request):
  return render(request, 'dashboard/accounts.html')


def createAccount(request):
  if request.method == 'POST':
    form = BankAccountForm(request.POST)
    if form.is_valid():
      pass
  else:
    form = BankAccountForm() 
  return render(request, 'dashboard/createAccount.html', {"form": form})

def logout(request):
  logout_auth(request)
  return redirect("/")

def login(request):
  if request.method == 'POST':
    form = AuthenticationForm(request.POST)
    if form.is_valid():
      email = form.cleaned_data.get('email')
      raw_password = form.cleaned_data.get('password1')
      user = authenticate(username=email, password=raw_password)
      print(user, email, raw_password)
      if user is not None:
        # if user.is_active:
        login_auth(request, user)
        return redirect('/')
      else:
        messages.error(request,'El correo electrónico o la contraseña son invalidos.')
        return redirect('login')
  else:
    form = AuthenticationForm()
  return render(request, 'registration/login.html', {'form': form})

def signup(request):
  if request.method == 'POST':
    form = SignUpForm(request.POST)
    if form.is_valid():
      form.save()
      email = form.cleaned_data.get('email')
      raw_password = form.cleaned_data.get('password1')
      user = authenticate(username=email, password=raw_password)
      login_auth(request, user)
      return redirect('/')
  else:
    form = SignUpForm()
  return render(request, 'registration/signup.html', {'form': form})