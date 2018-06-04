from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse, Http404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import logout as logout_auth
from django.contrib.auth import login as login_auth
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.forms import formset_factory
from io import BytesIO
from django.utils import timezone
from django.urls import reverse
import json
import time
from app.forms import *
from app.models import *
import requests
from django.db.models import Q


## Pair: BTCUSD, USDBTC, DASHUSD, etc
class PriceRetriever:
  def __init__(self):
    self.localbitcoins = json.loads(requests.get('https://localbitcoins.com//bitcoinaverage/ticker-all-currencies/').content)
    self.uphold = json.loads(requests.get('https://api.uphold.com/v0/ticker').content)

  def askUpholdPair(request, pair):
    for i in self.uphold:
      if i['pair'] == pair:
        return i['ask']

  def getPriceInformation():
    localbitcoins_BTC_USD = self.localbitcoins["USD"]["avg_12h"]
    uphold_BTC_USD = askUpholdPair(uphold, "BTCUSD")
    uphold_USD_BTC = askUpholdPair(uphold, "USDBTC")
    uphold_ETH_USD = askUpholdPair(uphold, "ETHUSD")
    uphold_USD_ETH = askUpholdPair(uphold, "USDETH")

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
    print(request.user.canVerify())
    if request.user.canVerify():
      message = ''' Su cuenta no esta verificada. Para poder realizar una operación es necesario que verifique su cuenta.
            <a href=" '''+ reverse('userVerification') + '''"> 
              <button class="btn btn-primary"> 
                Verificar ahora 
              </button>
            </a>'''
      messages.error(request, message, extra_tags="safe alert-warning")
    return render(request, 'dashboard.html')
  else:
    return render(request, 'index.html')

def company(request):
  return render(request, 'company.html')

def profile(request):
  if request.method == 'POST':
    emailForm = ChangeEmailForm(request.POST)
    passwordForm = PasswordChangeForm(data=request.POST, user=request.user)

    if request.POST['email'] != "":
      if emailForm.is_valid():
        email = emailForm.cleaned_data['email']
        if email == request.user.email:
          messages.error(request, "El email que ingresó ya se encuentra asociado a su cuenta.", extra_tags="alert-warning")
        elif not User.objects.filter(email=email):
          request.user.email = email
          request.user.save()
          messages.error(request, "Su email ha sido actualizado.", extra_tags="alert-success")
        else:
          messages.error(request, "El email que intentó ingresar ya se encuentra asociado a otro usuario.", extra_tags="alert-warning")
      else:
        messages.error(request, 'Email inválido. Intente nuevamente.', extra_tags="alert-warning")
    elif request.POST['old_password'] != "":
      if passwordForm.is_valid():
        passwordForm.save()
        update_session_auth_hash(request, passwordForm.user)
        messages.error(request, "Se cambió la contraseña exitosamente.", extra_tags="alert-success")
      else:
        messages.error(request, "No se ha podido cambiar la contraseña.", extra_tags="alert-warning")
    else:
      messages.error(request, "Un error ha ocurrido. Intente nuevamente.", extra_tags="alert-error")

  return render(request, 'dashboard/profile.html')

def userVerification(request):
  if request.user.canVerify():
    if request.method == 'POST':
      if 'file1' in request.FILES and 'file2' in request.FILES:
        file1 = request.FILES['file1']
        file2 = request.FILES['file2']
        if file1.name.endswith(('.png', 'jpeg', 'jpg')) and file2.name.endswith(('.png', 'jpeg', 'jpg')):
          request.user.id_front = file1
          request.user.selfie_image = file2
          request.user.save()
          return render(request, 'dashboard/verificationConfirmation.html')      
        else:
          messages.error(request, 'Solo puede subir imágenes PNG y JPG.', extra_tags="alert-error")
      else:
        messages.error(request, 'Por favor suba las imágenes.', extra_tags="alert-error")
    return render(request, 'dashboard/userVerification.html')
  else:
    return redirect('/')

def createOperation(request):
  abt = AccountBelongsTo.objects.filter(id_client=request.user.id)
  queryset1 = abt.filter(email__isnull=True)
  queryset2 = abt.exclude(email__isnull=True)

  ToAccountFormSet = formset_factory(ToAccountForm)
  
  rates = {}
  for i in ExchangeRate.objects.all():
    rates[str(i)] = i.rate

  fromAccs = {}
  for i in queryset1:
    fromAccs[i.id_account.id] = { 
      'currency':str(i.id_account.id_bank.currency),
      'name': str(i)
    }

  toAccs = {}
  for i in queryset2:
    toAccs[i.id_account.id] = {
      'currency':str(i.id_account.id_bank.currency),
      'name': str(i)
    }

  fee = 0.01

  if request.method == 'POST':
    POST = request.POST.copy()
    form1 = FromAccountForm(request.POST).setQueryset(queryset1)

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
        fromCurrency = fromAccount.id_account.id_bank.currency
        toCurrency = form1.cleaned_data['currency']
        rate = rates[str(fromCurrency) + "/" + str(toCurrency)]
        operation = Operation(fiat_amount = total,
                              crypto_rate = None,
                              status = 'Falta verificacion',
                              exchanger = None,
                              date = timezone.now(),
                              id_client = request.user,
                              id_account = fromAccount.id_account,
                              exchange_rate = rate,
                              origin_currency = fromCurrency,
                              target_currency = toCurrency,
                              date_creation = datetime.datetime.now()
                            )
        operation.save()
        for i in toAccounts:
          OperationGoesTo(operation_code = operation, number_account = i[0].id_account, amount = i[1] ).save()

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
  

  return render(request, 'dashboard/createOperation.html', {
                'form1': form1,
                'form2': form2,
                'rate': str(json.dumps(rates)),
                'toAccs': str(json.dumps(toAccs)),
                'fromAccs': str(json.dumps(fromAccs)),
                "fee": str(fee)})


def pendingOperations(request):
  operations = Operation.objects.filter(id_client=request.user)
  pending = operations.exclude(status="Fondos transferidos")
  complete = operations.filter(status="Fondos transferidos")
  return render(request, 'dashboard/pendingOperations.html', {'pendingOperations':pending, 'completeOperations':complete}) 


def operationModal(request, _operation_id):
  print(_operation_id)
  operation = Operation.objects.get(code=_operation_id)
  ogt = OperationGoesTo.objects.filter(operation_code = operation)
  if operation:
    return render(request, 'dashboard/operationModal.html', {'operation':operation, 'ogt': ogt}) 
  else: 
    return

def uploadImage(request, _operation_id):
  msg = ""
  
  try: operation = Operation.objects.get(code=_operation_id)
  except: raise Http404
  print(operation.id_client.id != request.user.id)
  print(operation.status != "Falta verificacion")
  if operation.id_client.id != request.user.id:
    raise PermissionDenied
  elif operation.status != "Falta verificacion":
    messages.error(request, 'Esta operacion ya fue verificada', extra_tags="alert-error")
    return render(request, 'dashboard/uploadImage.html', {"id": _operation_id})  

  if request.method == 'POST':
    if 'file' in request.FILES:
      file = request.FILES['file']
      if file.name.endswith(('.png', 'jpeg', 'jpg')):
        operation.status = "Por verificar"
        operation.save()
        ogt = OperationGoesTo.objects.all()
        for i in ogt:
          trans = Transaction(date = timezone.now(),
                              operation_type = "TO",
                              transfer_image = file,
                              origin_account = operation.id_account,
                              target_account = i.number_account )
          trans.save()
        return render(request, 'dashboard/verificationConfirmation.html')      
      else:
        messages.error(request, 'Solo puede subir imagenes PNG y JPG.', extra_tags="alert-error")
    else:
      messages.error(request, 'Por favor suba una imagen.', extra_tags="alert-warning")
  return render(request, 'dashboard/uploadImage.html', {"id": _operation_id})  



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
          messages.error(request,'Esta cuenta ya se encuentra asociada', extra_tags="alert-warning")
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
        messages.error(request,'El correo electrónico o la contraseña son inválidos.', extra_tags="alert-error")
        return redirect('login')
  else:
    form = AuthenticationForm()
  return render(request, 'registration/login.html', {'form': form})

def signup(request):
    tmpCountries = Country.objects.all()
    allCountries = [(tmp.name, tmp.name) for tmp in tmpCountries]
    allCountries.append(('Otro', 'Otro'))

    if request.method == 'POST':
        form = SignUpForm(request.POST, countriesC=allCountries)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=email, password=raw_password)
            login_auth(request, user)
            return redirect('/')
    else:
        form = SignUpForm(countriesC=allCountries)

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
                messages.error(request,msg, extra_tags="alert-warning")
                return render(request, 'admin/addCurrency.html', {'form': form})

            new_currency = Currency()
            new_currency.code = code
            new_currency.name = name
            new_currency.currency_type = currency_type

            new_currency.save()

            form.clean()

            msg = "La moneda fue agregada con éxito"
            messages.error(request, msg, extra_tags="alert-success")
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
            name = form.cleaned_data['name']
            if (Currency.objects.filter(name=name).exists()):
                msg = "El nombre de la moneda ingresado ya existe. Intente con uno diferente."
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/editCurrency.html', {'form': form})

            c.name = name
            c.currency_type = form.cleaned_data['currency_type']
            c.save()

            msg = "La moneda se editó con éxito."
            messages.error(request, msg, extra_tags="alert-success")
    else:    
        form = EditCurrencyForm(initial={'code': c.code, 'name': c.name, 'currency_type': c.currency_type})

    return render(request, 'admin/editCurrency.html', {'form': form})

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
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addExchangeRate.html', {'form': form})

            if (origin == target):
                msg = "Las monedas no pueden ser iguales. Elija otras monedas."
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addExchangeRate.html', {'form': form})

            new_exchange = ExchangeRate()
            new_exchange.rate = rate
            new_exchange.origin_currency = origin
            new_exchange.target_currency = target
            new_exchange.date = timezone.now()

            new_exchange.save()

            msg = "La tasa de cambio fue agregada con éxito"
            messages.error(request, msg, extra_tags="alert-success")
            return render(request, 'admin/addExchangeRate.html', {'form': form})
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
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editExchangeRate.html', {'form': form})

                if (origin == target):
                    msg = "Las monedas no pueden ser iguales. Elija otras monedas."
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editExchangeRate.html', {'form': form})

            actualRate.rate = rate
            actualRate.origin_currency = origin
            actualRate.target_currency = target
            actualRate.date = timezone.now()

            actualRate.save()

            msg = "La moneda fue editada con éxito"
            messages.error(request, msg, extra_tags="alert-success")
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

            if (Bank.objects.filter(swift=swift).exists()):
                msg = "El SWIFT ingresado corresponde a otro banco. Ingrese un SWIFT correcto."
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addBank.html', {'form': form})
            if (Bank.objects.filter(aba=aba).exists()):
                msg = "El ABA ingresado corresponde a otro banco. Ingrese un ABA correcto."
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addBank.html', {'form': form})

            new_bank = Bank()
            new_bank.name = name.upper()
            new_bank.country = country
            new_bank.swift = swift
            new_bank.aba = aba
            new_bank.save()

            msg = "El banco fue agregado con éxito."
            messages.error(request, msg, extra_tags="alert-success")
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

            if (Bank.objects.filter(aba=aba).exists()):
                msg = "El ABA ingresado corresponde a otro banco. Ingrese un ABA correcto."
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/editBank.html', {'form': form})

            actualBank.country = country.upper()
            actualBank.name = name.upper()
            actualBank.aba = aba
            actualBank.save()

            msg = "El banco fue editado con éxito."
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = EditBankForm(initial={'name': actualBank.name, 'country': actualBank.country, 'swift':_bank_id,
                                      'aba': actualBank.aba}, countriesC=allCountries)

        return render(request, 'admin/editBank.html', {'form': form})

def addAccount(request):
    tmp_currencies = Currency.objects.all()
    all_currencies = [(tmp.code, tmp.name) for tmp in tmp_currencies]

    if (request.method == 'POST'):
        form = NewAccountForm(request.POST, currencyC=all_currencies)

        if (form.is_valid()):
            number = form.cleaned_data['number']
            is_thirds = forms.cleaned_data['is_thirds']
            use_type = forms.cleaned_data['use_type']
            bank = Bank.objects.get(swift=form.cleaned_data['bank'])
            currency = Currency.objects.get(code=form.cleaned_data['currency'])

            if (Account.objects.filter(number=number,bank=bank).exists()):
                msg = "La cuenta que ingresaste ya existe en ese banco."
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addAccount.html', {'form': form})

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
            messages.error(request, msg, extra_tags="alert-success")

    else:
        form = NewAccountForm(currencyC=all_currencies)

    return render(request, 'admin/addAccount.html', {'form': form})

def adminAccount(request):
    if (request.method == 'GET'):
        all_accounts = Account().objects.all()

        return render(request, 'admin/adminAccount.html', {'accounts': all_accounts})

def editAccount(request, _account_id):
    try:
        actualAccount = Account.objects.get(id=_account_id)
    except:
        raise Http404

    tmp_currencies = Currency.objects.all()
    all_currencies = [(tmp.code, tmp.name) for tmp in tmp_currencies]

    if (request.method == 'POST'):
        form = NewAccountForm(request.POST, currencyC=allCurrencies)

        if (form.is_valid()):
            number = form.cleaned_data['number']
            is_thirds = forms.cleaned_data['is_thirds']
            use_type = forms.cleaned_data['use_type']
            bank = Bank.objects.get(swift=form.cleaned_data['bank'])
            currency = Currency.objects.get(code=form.cleaned_data['currency'])

            if (Account.objects.filter(number=number,bank=bank).exists()):
                msg = "La cuenta que ingresaste ya existe en ese banco."
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/editAccount.html', {'form': form})

            actualAccount.number = number
            actualAccount.id_bank = bank
            actualAccount.id_currency = currency

            belongTo = AccountBelongsTo.objects.filter(id_account=actualAccount, id_client=_client_id)
            if (is_thirds == 'Terceros'):
                belongs_to.owner = form.cleaned_data['owner']
                belongs_to.alias = form.cleaned_data['alias']
                belongs_to.email = form.cleaned_data['email']
                belongs_to.id_number = form.cleaned_data['id_number']

            elif ((is_thirds != 'Terceros') and (belongTo.owner != None)):
                belongs_to.owner = None
                belongs_to.alias = None
                belongs_to.email = None
                belongs_to.id_number = None

            belongTo.save()

            actualAccount.is_client = (is_thirds == 'Cliente')
            actualAccount.save()
            #Falta el cliente

    else:
        form = NewAccountForm(currencyC=allCurrencies)

    return render(request, 'admin/editAccount.html', {'form': form})


def addUser(request):
    tmpAllies = User.objects.filter(Q(user_type='Aliado-1') | Q(user_type='Aliado-2') | Q(user_type='Aliado-3'))
    allAllies = [(tmp.id, tmp.first_name + ' ' + tmp.last_name + ' - ' + str(tmp.id_number)) for tmp in tmpAllies]
    allAllies.append(('Ninguno', 'Ninguno'))
    tmpCountries = Country.objects.all()
    allCountries = [(tmp.name, tmp.name) for tmp in tmpCountries]
    allCountries.append(('Otro', 'Otro'))

    if (request.method == 'POST'):
        form = NewUserForm(request.POST, alliesC=allAllies, countriesC=allCountries)

        if (form.is_valid()):
            new_mail = form.clean_email()
            if (User.objects.filter(email=new_mail).exists()):
                msg = "Ya existe un usuario con el correo ingresado."
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addUser.html', {'form': form})

            new_id = form.cleaned_data['id_number']
            new_country = form.cleaned_data['country']
            if (User.objects.filter(id_number=new_id, country=new_country).exists()):
                msg = "El número de identificación pertenece a otra persona."
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addUser.html', {'form': form})

            new_user = User()

            new_user.first_name = form.clean_first_name()
            new_user.last_name = form.clean_last_name()
            new_user.email = new_mail
            new_user.mobile_phone = form.cleaned_data['mobile_phone']
            new_user.country = form.cleaned_data['country']
            new_user.address = form.cleaned_data['address']
            new_user.user_type = form.cleaned_data['user_type']
            new_user.canBuyDollar = form.cleaned_data['canBuyDollar']
            new_referred_id = form.cleaned_data['referred_by']

            if (new_referred_id == 'Ninguno'):
                new_user.referred_by = None
            else:
                newAllie = User.objects.get(id=new_referred_id)
                new_user.referred_by = newAllie

            new_user.save()

            msg = "El usuario fue agregado con éxito."
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewUserForm(alliesC=allAllies, countriesC=allCountries)

    return render(request, 'admin/addUser.html', {'form': form})

def adminUser(request):
    if (request.method == 'GET'):
        all_users = User.objects.all()

        return render(request, 'admin/adminUser.html', {'users': all_users})

def editUser(request, _user_id):
    try:
        actualUser = User.objects.get(id=_user_id)
    except:
        raise Http404

    tmpAllies = User.objects.filter(Q(user_type='Aliado-1') | Q(user_type='Aliado-2') | Q(user_type='Aliado-3'))
    allAllies = [(tmp.id, tmp.first_name + ' ' + tmp.last_name + ' - ' + str(tmp.id_number)) for tmp in tmpAllies]
    allAllies.append(('Ninguno', 'Ninguno'))
    tmpCountries = Country.objects.all()
    allCountries = [(tmp.name, tmp.name) for tmp in tmpCountries]
    allCountries.append(('Otro', 'Otro'))

    if (request.method == 'POST'):
        form = NewUserForm(request.POST, alliesC=allAllies, countriesC=allCountries)

        if (form.is_valid()):    
            new_mail = form.clean_email()
            if (new_mail != actualUser.email):
                if (User.objects.filter(email=new_mail).exists()):
                    msg = "Ya existe un usuario con el correo ingresado."
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editUser.html', {'form': form})
                actualUser.email = new_mail

            new_id = form.cleaned_data['id_number']
            new_country = form.cleaned_data['country']
            print(new_id==actualUser.id_number)
            if (new_id != actualUser.id_number):
                if (User.objects.filter(id_number=new_id, country=new_country).exists()):
                    msg = "El número de identificación pertenece a otra persona."
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editUser.html', {'form': form})
                actualUser.id_number = new_id

            actualUser.first_name = form.clean_first_name()
            actualUser.last_name = form.clean_last_name()
            actualUser.mobile_phone = form.cleaned_data['mobile_phone']
            actualUser.country = form.cleaned_data['country']
            actualUser.address = form.cleaned_data['address']
            actualUser.user_type = form.cleaned_data['user_type']
            actualUser.canBuyDollar = form.cleaned_data['canBuyDollar']
            new_referred_id = form.cleaned_data['referred_by']

            if (new_referred_id == 'Ninguno'):
                actualUser.referred_by = None
            elif ((actualUser.referred_by == None) or (new_referred_id != actualUser.referred_by.id)):
                newAllie = User.objects.get(id=new_referred_id)
                actualUser.referred_by = newAllie

            actualUser.save()

            msg = "El usuario fue editado con éxito."
            messages.error(request, msg, extra_tags="alert-success")
        else:
            print(form.errors)
    else:
        if not(actualUser.referred_by):
            referred = 'Ninguno'
        else:
            referred = actualUser.referred_by.first_name + " " + actualUser.referred_by.last_name + " - " + actualUser.referred_by.id_number
        form = NewUserForm(alliesC=allAllies, countriesC=allCountries,
                            initial={'first_name': actualUser.first_name, 'last_name': actualUser.last_name, 'mobile_phone': actualUser.mobile_phone,
                                    'country': actualUser.country, 'address': actualUser.address, 'id_number': actualUser.id_number, 'user_type': actualUser.user_type, 
                                    'referred_by': actualUser.referred_by, 'canBuyDollar': actualUser.canBuyDollar, 'email': actualUser.email})

    return render(request, 'admin/editUser.html', {'form': form})

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
                msg = "Ya existe un feriado para ese día en " + country
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addHoliday.html', {'form': form})

            new_holiday = Holiday()
            new_holiday.date = date
            new_holiday.description = description
            new_holiday.country = country
            new_holiday.save()

            msg = "El feriado fue agregado con éxito."
            messages.error(request, msg, extra_tags="alert-success")
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
                    msg = "Ya existe un feriado para ese día en " + country
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editHoliday.html', {'form': form})        

            actualHoliday.date = date
            actualHoliday.description = description
            actualHoliday.country = country

            actualHoliday.save()

            msg = "El feriado fue editado con éxito."
            messages.error(request, msg, extra_tags="alert-success")
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
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addCountry.html', {'form': form})

            new_country = Country()
            new_country.name = name
            new_country.status = int(status)
            new_country.save()

            msg = "El país fue agregado con éxito."
            messages.error(request, msg, extra_tags="alert-success")
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
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editCountry.html', {'form': form})

                actualCountry.delete()
                actualCountry = Country()

            actualCountry.name = name
            actualCountry.status = int(status)

            msg = "El país fue editado con éxito."
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewCountryForm(initial={'name': actualCountry.name})

    return render(request, 'admin/editCountry.html', {'form': form})

def operationalDashboard(request):
    if (request.method == 'GET'):
        if ((request.user.user_type == 'Operador') or (request.user.user_type == 'Admin')):
            actualOperations = Operation.objects.filter(is_active=True).order_by('date')
            endedOperations = Operation.objects.filter(is_active=False).order_by('date')
            
        elif (request.user.user_type == 'Aliado-1'):
            actualOperations = Operation.objects.filter(Q(is_active=True) & (Q(id_allie_origin=request.user) | Q(id_allie_target=request.user))).order_by('date')
            endedOperations = Operation.objects.filter(Q(is_active=False) & (Q(id_allie_origin=request.user) | Q(id_allie_target=request.user))).order_by('date')

        totalOpen = actualOperations.count()
        totalEnded = endedOperations.count()

        return render(request, 'dashboard/operationalDashboard.html', 
                            {'actualO': actualOperations, 'endedO': endedOperations, 'totalOpen': totalOpen, 'totalEnded': totalEnded})

def operationDetailDashboard(request, _operation_id):
    pass

def operationEditDashboard(request, _operation_id):
    pass
