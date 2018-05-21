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
          messages.error(request, "El email que intento ingresar ya se encuentra asociado a otro usuario.", extra_tags="alert-warning")
      else:
        messages.error(request, 'Email invalido. Intente nuevamente.', extra_tags="alert-warning")
    elif request.POST['old_password'] != "":
      if passwordForm.is_valid():
        passwordForm.save()
        update_session_auth_hash(request, passwordForm.user)
        messages.error(request, "Se cambio la contraseña exitosamente.", extra_tags="alert-success")
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
          messages.error(request, 'Solo puede subir imagenes PNG y JPG.', extra_tags="alert-error")
      else:
        messages.error(request, 'Por favor suba las imagenes.', extra_tags="alert-error")
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
                              target_currency = toCurrency
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
        messages.error(request,'El correo electrónico o la contraseña son invalidos.', extra_tags="alert-error")
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
        form = NewCurrencyForm(request.POST)

        if (form.is_valid()):
            code = form.cleaned_data['code']
            if (code != c.code):
                if (Currency.objects.filter(code=code).exists()):
                    msg = "El código de la moneda ingresado ya existe. Intente con uno diferente."

                    return render(request, 'admin/editCurrency.html', {'form': form, 'msg': msg, 'c': c})
                c.delete()
                c = Currency()

            c.code = code
            c.name = form.cleaned_data['name']
            c.currency_type = form.cleaned_data['currency_type']
            c.save()

            msg = "La moneda se editó con éxito."
            return render(request, 'admin/editCurrency.html', {'form': form, 'msg': msg, 'c': c})
    else:    
        form = NewCurrencyForm(initial={'code': c.code, 'name': c.name, 'currency_type': c.currency_type})

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
            new_exchange.date = timezone.now()

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
            actualRate.date = timezone.now()

            actualRate.save()

            msg = "La moneda fue editada con éxito"
            return render(request, 'admin/editExchangeRate.html', {'form': form, 'msg': msg})
    else:
        form = NewExchangeRateForm(initial={'rate':actualRate.rate, 'origin_currency': actualRate.origin_currency.code, 'target_currency': actualRate.target_currency.code},
                                        currencyC=allCurrencies)

    return render(request, 'admin/editExchangeRate.html', {'form': form})



def handler403(request):
  return render(request,'error_handling/page_403.html')

def handler404(request):
  return render(request,'error_handling/page_404.html')

def handler500(request):
  return render(request,'error_handling/page_500.html')
