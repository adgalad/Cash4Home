from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth import logout as logout_auth
from django.contrib.auth import login as login_auth
from django.contrib import messages
from io import BytesIO
import time
import datetime

from app.forms import *
from app.models import *

def home(request):
    if request.user.is_authenticated():
        return render(request, 'dashboard.html')
    else:
        return render(request, 'index.html')

def company(request):
  return render(request, 'company.html')

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
        pass
        # Raise 404 error

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
        pass
        # Raise 404 error

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
    if (request.method == 'POST'):
        form = NewBankForm(request.POST)

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
            new_bank.country = country.upper()
            new_bank.swift = swift
            new_bank.aba = aba
            new_bank.save()

            msg = "El banco fue agregado con éxito."
            return render(request, 'admin/addBank.html', {'form': form, 'msg': msg})
    else:
        form = NewBankForm()

    return render(request, 'admin/addBank.html', {'form': form})

def adminBank(request):
    if (request.method == 'GET'):
        all_banks = Bank.objects.all()

        return render(request, 'admin/adminBank.html', {'banks': all_banks})

def editBank(request, _bank_id):
    try:
        actualBank = Bank.objects.get(id=_bank_id)
    except:
        pass
        # Raise 404 error

    if (request.method == 'POST'):
        form = EditBankForm(request.POST)

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
        form = EditBankForm()

        return render(request, 'admin/editBank.html', {'form': form})

def addAccount(request):
    pass

def adminAccount(request):
    if (request.method == 'GET'):
        all_accounts = Account().objects.all()

        return render(request, 'admin/adminAccount.html', {'accounts': all_accounts})

def editAccount(request):
    pass