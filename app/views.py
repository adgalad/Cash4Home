from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import logout as logout_auth
from django.contrib.auth import login as login_auth
from django.contrib import messages
from django.forms import formset_factory
from io import BytesIO
import time
import datetime

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
  abt = AccountBelongsTo.objects.filter(id_client=request.user.id)
  queryset1 = abt.filter(email__isnull=True)
  queryset2 = abt.exclude(email__isnull=True)
  ToAccountFormSet = formset_factory(ToAccountForm)

  if request.method == 'POST':
    POST = request.POST.copy()
    form1 = FromAccountForm(POST).setQueryset(queryset1)

    POST['form-TOTAL_FORMS' ] = 5
    POST['form-INITIAL_FORMS'] = 5
    POST['form-MAX_NUM_FORMS'] = 5
    form2 = ToAccountFormSet(POST)
    for i in form2:
      i.setQueryset(queryset2)

    if form1.is_valid() and form2.is_valid():
      fromAccount = form1.cleaned_data["account"]
      toAccounts = []
      ok = True
      total = 0
      for i in form2:
        acc = i.cleaned_data["account"]
        amount = i.cleaned_data["amount"]
        if acc and amount > 0:
          toAccounts.append((acc, amount))
          total += amount
        elif acc is None and amount <= 0:
          pass
        else:
          ok = False
          break

      if ok:
        operation = Operation(code = str(datetime.datetime.now()),
                              fiat_amount = total,
                              crypto_rate = None,
                              status = 'Por verificar',
                              exchanger = None,
                              date = datetime.datetime.now(),
                              id_client = request.user,
                              id_account = fromAccount.id_account,
                              exchange_rate = 90.0,
                              origin_currency = Currency.objects.get(code="USD"),
                              target_currency = Currency.objects.get(code="VEF")
                            )
        operation.save()
        for i in toAccounts:
          transaction = Transaction(code = str(datetime.datetime.now()),
                                    date = datetime.datetime.now(),
                                    operation_type = 'TD',
                                    transfer_image = None,
                                    origin_account = fromAccount.id_account,
                                    target_account = i[0].id_account
                                  )
          transaction.save()


        return redirect("/")

  else:
    form1 = FromAccountForm().setQueryset(queryset1)
    data = {
      'form-TOTAL_FORMS': '5',
      'form-INITIAL_FORMS': '5',
      'form-MAX_NUM_FORMS': '5',
    }
    
    form2 = ToAccountFormSet(data)
    for i in form2:
      i.setQueryset(queryset2)

  rate = { 1: { 2: 0.7, 3:800000, 'name':"USD"},
           2: { 1: 1.6, 3:1000000, 'name':"EUR"},
           3: { 1: 0.00000125, 2:0.000001, 'name':"VEF"}}

  fee = 0.01

  return render(request, 'dashboard/createOperation.html', {'form1': form1, 'form2': form2, "rate":str(json.dumps(rate)), "fee": str(fee)})

def uploadImage(request):
  if request.method == 'POST':
    print(request.FILES)
    
  return render(request, 'dashboard/uploadImage.html')  

@login_required
def accounts(request):

  abt = AccountBelongsTo.objects.filter(id_client=request.user.id)
  origin = []
  dest = []
  for i in abt:
    if i.id_account.use_type == "Origen":
      origin.append(i)
    else:
      dest.append(i)

  return render(request, 'dashboard/accounts.html', {'origin':origin, 'dest':dest})


def createAccount(request):
  own = request.GET.get('own')

  if own is None:
    return render(request, 'error_handling/page_404.html')
  own = own == "1"
  form = BankAccountForm if own else BankAccountDestForm

  if request.method == 'POST':
    form = form(request.POST)
    if form.is_valid():
      number = form.cleaned_data.get('number')
      bank = form.cleaned_data.get('bank')
      acc = Account.objects.filter(number=number, id_bank=bank)
      print(number, bank)
      if acc.count() == 0:
        acc = Account(number=number, id_bank=bank, use_type="Origen" if own else "Destino", is_client=True)
      else:
        acc = acc[0]
        acc.is_client = own

      if AccountBelongsTo.objects.filter(id_client=request.user.id).filter(id_account=acc.id).count() > 0:
          messages.error(request,'Esta cuenta ya se encuentra asociada')
          return redirect("/account/new?own="+request.GET.get('own'))
      acc.save()

      if own:
        AccountBelongsTo.objects.create(id_client=request.user, id_account=acc)
      else:
        email = form.cleaned_data.get('email').lower()
        alias = form.cleaned_data.get('alias')
        owner = form.cleaned_data.get('owner').title()
        id_number = form.cleaned_data.get('id_number')
        AccountBelongsTo.objects.create(id_client=request.user, 
                                        id_account=acc,
                                        email=email,
                                        alias=alias,
                                        owner=owner,
                                        id_number=id_number)
        
      
      return redirect('accounts')
  else:
    form = form() 
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


def handler404(request):
  return render(request,'error_handling/page_404.html')


def handler500(request):
  return render(request,'error_handling/page_500.html')

