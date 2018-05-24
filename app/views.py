from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse, Http404
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
from app.models import *

########## ERROR HANDLING ##########

#---- Vista para manejar Error 404 - Not found ----#
def handler404(request):
    response = render(request, 'error_handling/404.html')
    response.status_code = 404
    return response

#---- Vista para manejar Error 403 - Permission denied ----#
def handler403(request):
    response = render(request, 'error_handling/403.html')
    response.status_code = 403
    return response

#---- Vista para manejar Error 500 - Internal server error ----#
def handler500(request):
    response = render(request, 'error_handling/500.html')
    response.status_code = 500
    return response

########## FIN ERROR HANDLING ##########

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


# Admin views

def addCurrencies(request):
    if (request.method == 'POST'):
        form = NewCurrencyForm(request.POST)

        if (form.is_valid()):
            code = form.cleaned_data['code']
            name =  form.cleaned_data['name']
            currency_type = form.cleaned_data['currency_type']

            alreadyExists = Currency.objects.filter(code=code).exists()

            if (alreadyExists):
                msg = "La moneda ingresada ya existe. Elija otro nombre."
                return render(request, 'admin/addCurrency.html', {'form': form, 'msg': msg})

            new_currency = Currency()
            new_currency.code = code
            new_currency.name = name
            new_currency.currency_type = currency_type

            new_currency.save()

            msg = "La moneda fue agregada con éxito"
            return render(request, 'admin/addCurrency.html', {'form': form, 'msg': msg})
    else:
        form = NewCurrencyForm()

    return render(request, 'admin/addCurrency.html', {'form': form})


def adminCurrencies(request):
    if (request.method == 'GET'):
        allCurrencies = Currency.objects.all()

        return render(request, 'admin/adminCurrency.html', {'currencies': allCurrencies})

def editCurrencies(request, _currency_id):
    try:
        c = Currency.objects.get(code=_currency_id)
    except:
        raise Http404

    if (request.method == 'POST'):
        form = EditCurrencyForm(request.POST)

        if (form.is_valid()):
            c.name = form.cleaned_data['name']
            if (Currency.objects.filter(name=name).exists()):
                msg = "El nombre de la moneda ingresado ya existe. Intente con uno diferente."

                return render(request, 'admin/editCurrency.html', {'form': form, 'msg': msg, 'c': c})

            c.currency_type = form.cleaned_data['currency_type']
            c.save()

            msg = "La moneda se editó con éxito."
            return render(request, 'admin/editCurrency.html', {'form': form, 'msg': msg, 'c': c})
    else:    
        form = EditCurrencyForm(initial={'code': c.code, 'name': c.name, 'currency_type': c.currency_type})

    return render(request, 'admin/editCurrency.html', {'form': form, 'c': c})

def addExchangeRate(request):
    tmpCurrencies = Currency.objects.all()
    allCurrencies = [(tmp.code, tmp.code) for tmp in tmpCurrencies]

    if (request.method == 'POST'):
        form = NewExchangeRateForm(request.POST, currencyC=allCurrencies)

        if (form.is_valid()):
            rate = form.cleaned_data['rate']
            origin =  Currency.objects.get(code=form.cleaned_data['origin_currency'])
            target = Currency.objects.get(code=form.cleaned_data['target_currency'])

            alreadyExists = ExchangeRate.objects.filter(origin_currency=origin, target_currency=target).exists()

            if (alreadyExists):
                msg = "La tasa de cambio ingresada ya existe. Elija otras monedas."
                return render(request, 'admin/addExchangeRate.html', {'form': form, 'msg': msg})

            if (origin == target):
                msg = "Las monedas no pueden ser iguales. Elija otras monedas."
                return render(request, 'admin/addExchangeRate.html', {'form': form, 'msg': msg})

            new_exchange = ExchangeRate()
            new_exchange.rate = rate
            new_exchange.origin_currency = origin
            new_exchange.target_currency = target
            new_exchange.date = datetime.datetime.now()

            new_exchange.save()

            msg = "La moneda fue agregada con éxito"
            return render(request, 'admin/addExchangeRate.html', {'form': form, 'msg': msg})
    else:
        form = NewExchangeRateForm(currencyC=allCurrencies)

    return render(request, 'admin/addExchangeRate.html', {'form': form})

def adminExchangeRate(request):
    if (request.method == 'GET'):
        allRates = ExchangeRate.objects.all()

        return render(request, 'admin/adminExchangeRate.html', {'rates': allRates})

def editExchangeRate(request, _rate_id):
    try:
        actualRate = ExchangeRate.objects.get(id=_rate_id)
    except:
        raise Http404

    tmpCurrencies = Currency.objects.all()
    allCurrencies = [(tmp.code, tmp.code) for tmp in tmpCurrencies]

    if (request.method == 'POST'):
        form = NewExchangeRateForm(request.POST, currencyC=allCurrencies)

        if (form.is_valid()):
            rate = form.cleaned_data['rate']
            origin =  Currency.objects.get(code=form.cleaned_data['origin_currency'])
            target = Currency.objects.get(code=form.cleaned_data['target_currency'])


            if ((origin != actualRate.origin_currency) or (target != actualRate.target_currency)):
                alreadyExists = ExchangeRate.objects.filter(origin_currency=origin, target_currency=target).exists()

                if (alreadyExists):
                    msg = "La tasa de cambio ingresada ya existe. Elija otras monedas."
                    return render(request, 'admin/editExchangeRate.html', {'form': form, 'msg': msg})

                if (origin == target):
                    msg = "Las monedas no pueden ser iguales. Elija otras monedas."
                    return render(request, 'admin/editExchangeRate.html', {'form': form, 'msg': msg})

            actualRate.rate = rate
            actualRate.origin_currency = origin
            actualRate.target_currency = target
            actualRate.date = datetime.datetime.now()

            actualRate.save()

            msg = "La moneda fue editada con éxito"
            return render(request, 'admin/editExchangeRate.html', {'form': form, 'msg': msg})
    else:
        form = NewExchangeRateForm(initial={'rate':actualRate.rate, 'origin_currency': actualRate.origin_currency.code, 'target_currency': actualRate.target_currency.code},
                                        currencyC=allCurrencies)

    return render(request, 'admin/editExchangeRate.html', {'form': form})

def addBank(request):
    tmpCountries = Country.objects.all()
    allCountries = [(tmp.name, tmp.name) for tmp in tmpCountries]

    if (request.method == 'POST'):
        form = NewBankForm(request.POST, countriesC=allCountries)

        if (form.is_valid()):
            name = form.cleaned_data['name']
            country = form.cleaned_data['country']
            swift = form.cleaned_data['swift']
            aba = form.cleaned_data['aba']

            if (Bank().objects.filter(swift=swift).exists()):
                msg = "El SWIFT ingresado corresponde a otro banco. Ingrese un SWIFT correcto."
                return render(request, 'admin/addBank.html', {'form': form, 'msg': msg})
            if (Bank().objects.filter(aba=aba).exists()):
                msg = "El ABA ingresado corresponde a otro banco. Ingrese un ABA correcto."
                return render(request, 'admin/addBank.html', {'form': form, 'msg': msg})

            new_bank = Bank()
            new_bank.name = name.upper()
            new_bank.country = country
            new_bank.swift = swift
            new_bank.aba = aba
            new_bank.save()

            msg = "El banco fue agregado con éxito."
            return render(request, 'admin/addBank.html', {'form': form, 'msg': msg})
    else:
        form = NewBankForm(countriesC=allCountries)

    return render(request, 'admin/addBank.html', {'form': form})

def adminBank(request):
    if (request.method == 'GET'):
        all_banks = Bank.objects.all()

        return render(request, 'admin/adminBank.html', {'banks': all_banks})

def editBank(request, _bank_id):
    tmpCountries = Country.objects.all()
    allCountries = [(tmp.name, tmp.name) for tmp in tmpCountries]

    try:
        actualBank = Bank.objects.get(swift=_bank_id)
    except:
        raise Http404

    if (request.method == 'POST'):
        form = EditBankForm(request.POST, countriesC=allCountries)

        if (form.is_valid()):
            country = form.cleaned_data['country']
            name = form.cleaned_data['name']
            aba = form.cleaned_data['aba']

            if (Bank().objects.filter(aba=aba).exists()):
                msg = "El ABA ingresado corresponde a otro banco. Ingrese un ABA correcto."
                return render(request, 'admin/editBank.html', {'form': form, 'msg': msg})

            actualBank.country = country.upper()
            actualBank.name = name.upper()
            actualBank.aba = aba
            actualBank.save()

            msg = "El banco fue editado con éxito."
            return render(request, 'admin/editBank.html', {'form': form, 'msg': msg})
    else:
        form = EditBankForm(initial={'name': actualBank.name, 'country': actualBank.country, 'swift':_bank_id,
                                      'aba': actualBank.aba}, countriesC=allCountries)

        return render(request, 'admin/editBank.html', {'form': form})

def addAccount(request):
    tmp_banks = Bank.objects.all()
    all_banks = [(tmp.swift, tmp.name) for tmp in tmp_banks]
    tmp_currencies = Currency.objects.all()
    all_currencies = [(tmp.code, tmp.name) for tmp in tmp_currencies]

    if (request.method == 'POST'):
        form = NewAccountForm(request.POST, currencyC=all_currencies, bankC=all_banks)

        if (form.is_valid()):
            number = form.cleaned_data['number']
            is_thirds = forms.cleaned_data['is_thirds']
            use_type = forms.cleaned_data['use_type']
            bank = Bank.objects.get(swift=form.cleaned_data['bank'])
            currency = Currency.objects.get(code=form.cleaned_data['currency'])

            if (Account.objects.filter(number=number,bank=bank).exists()):
                msg = "La cuenta que ingresaste ya existe en ese banco."
                return render(request, 'admin/addAccount.html', {'form': form, 'msg': msg})

            new_account = Account()
            new_account.number = number
            new_account.is_client = (is_thirds == 'Cliente')
            new_account.id_bank = bank
            new_account.id_currency = currency
            new_account.save()

            belongs_to = AccountBelongsTo()
            belongs_to.id_account = new_account
            #Falta el cliente
            if (is_thirds == 'Terceros'):
                belongs_to.owner = form.cleaned_data['owner']
                belongs_to.alias = form.cleaned_data['alias']
                belongs_to.email = form.cleaned_data['email']
                belongs_to.id_number = form.cleaned_data['id_number']

            belongs_to.save()

            msg = "La cuenta fue agregada con éxito."
            return render(request, 'admin/addAccount.html', {'form': form, 'msg': msg})

    else:
        form = NewAccountForm(currencyC=all_currencies, bankC=all_banks)

    return render(request, 'admin/addAccount.html', {'form': form})

def adminAccount(request):
    if (request.method == 'GET'):
        all_accounts = Account().objects.all()

        return render(request, 'admin/adminAccount.html', {'accounts': all_accounts})

def editAccount(request, _account_id):
    pass


def addUser(request):
    if (request.method == 'POST'):
        form = SignUpForm(request.POST)

        if (form.is_valid()):
            form.save()

            msg = "El usuario fue agregado con éxito."
            return render(request, 'admin/addUser.html', {'form': form, 'msg': msg})
    else:
        form = SignUpForm()

        return render(request, 'admin/addUser.html', {'form': form, 'msg': msg})

def adminUser(request):
    if (request.method == 'GET'):
        all_users = User.objects.all()

        return render(request, 'admin/adminUser.html', {'users': all_users})

def editUser(request, _user_id):
    try:
        actualUser = User.objects.get(id=_user_id)
    except:
        raise Http404

    if (request.method == 'POST'):
        pass
    else:
        pass

    return render(request, 'admin/editUser.html')

def addHoliday(request):
    tmpCountries = Country.objects.all()
    allCountries = [(tmp.name, tmp.name) for tmp in tmpCountries]

    if (request.method == 'POST'):
        form = NewHolidayForm(request.POST, countriesC=allCountries)

        if (form.is_valid()):
            date = form.cleaned_data['date']
            description = form.cleaned_data['description']
            country = form.cleaned_data['country']

            if (Holiday.objects.filter(date=date, country=country).exists()):
                msg = ("Ya existe un feriado para ese día en %s.", country)
                return render(request, 'admin/addHoliday.html', {'form': form, 'msg': msg})

            new_holiday = Holiday()
            new_holiday.date = date
            new_holiday.description = description
            new_holiday.country = country
            new_holiday.save()

            msg = "El feriado fue agregado con éxito."
            return render(request, 'admin/addHoliday.html', {'form': form, 'msg': msg})
    else:
        form = NewHolidayForm(countriesC=allCountries)

    return render(request, 'admin/addHoliday.html', {'form': form})

def adminHoliday(request):
    if (request.method == 'GET'):
        holidays = Holiday.objects.all()

        return render(request, 'admin/adminHoliday.html', {'holidays': holidays})

def editHoliday(request, _holiday_id):
    try:
        actualHoliday = Holiday.objects.get(id=_holiday_id)
    except:
        raise Http404

    tmpCountries = Country.objects.all()
    allCountries = [(tmp.name, tmp.name) for tmp in tmpCountries]

    if (request.method == 'POST'):
        form = NewHolidayForm(request.POST, countriesC=allCountries)

        if (form.is_valid()):
            date = form.cleaned_data['date']
            description = form.cleaned_data['description']
            country = form.cleaned_data['country']

            if ((actualHoliday.date != date) or (actualHoliday.country != country)):
                if (Holiday.objects.filter(date=date, country=country)):
                    msg = ("Ya existe un feriado para ese día en %s.", country)
                    return render(request, 'admin/editHoliday.html', {'form': form, 'msg': msg})        

            actualHoliday.date = date
            actualHoliday.description = description
            actualHoliday.country = country

            actualHoliday.save()

            msg = "El feriado fue editado con éxito."
            return render(request, 'admin/editHoliday.html', {'form': form, 'msg': msg})
    else:
        form = NewHolidayForm(initial={'date': actualHoliday.date, 'description': actualHoliday.description,
                                        'country': actualHoliday.country}, countriesC=allCountries)

    return render(request, 'admin/editHoliday.html', {'form': form})

def addCountry(request):
    if (request.method == 'POST'):
        form = NewCountryForm(request.POST)

        if (form.is_valid()):
            name = form.cleaned_data['name']
            status = form.cleaned_data['status']

            if (Country.objects.filter(name=name).exists()):
                msg = "Ya existe un país con ese nombre. Ingrese otro."
                return render(request, 'admin/addCountry.html', {'form': form, 'msg': msg})

            new_country = Country()
            new_country.name = name
            new_country.status = int(status)
            new_country.save()

            msg = "El país fue agregado con éxito."
            return render(request, 'admin/addCountry.html', {'form': form, 'msg': msg})
    else:
        form = NewCountryForm()

    return render(request, 'admin/addCountry.html', {'form': form})

def adminCountry(request):
    if (request.method == 'GET'):
        all_countries = Country.objects.all()

        return render(request, 'admin/adminCountry.html', {'countries': all_countries})

def editCountry(request, _country_id):
    try:
        actualCountry = Country.objects.get(name=_country_id)
    except:
        raise Http404

    if (request.method == 'POST'):
        form = NewCountryForm(request.POST)

        if (form.is_valid()):
            name = form.cleaned_data['name']
            status = form.cleaned_data['status']

            if (name != actualCountry.name):
                if (Country.objects.filter(name=name).exists()):
                    msg = "Ya existe un país con ese nombre. Ingrese otro"
                    return render(request, 'admin/editCountry.html', {'form': form, 'msg': msg})

                actualCountry.delete()
                actualCountry = Country()

            actualCountry.name = name
            actualCountry.status = int(status)

            msg = "El país fue editado con éxito."
            return render(request, 'admin/editCountry.html', {'form': form, 'msg': msg})
    else:
        form = NewCountryForm(initial={'name': actualCountry.name})

    return render(request, 'admin/editCountry.html', {'form': form})


