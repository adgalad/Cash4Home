from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse, Http404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth import logout as logout_auth
from django.contrib.auth import login as login_auth
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.core.mail import send_mail
from django.forms import formset_factory
from io import BytesIO
from django.utils import timezone
from django.urls import reverse
import json
import time
from app.forms import *
from app.models import *
import requests
from C4H.settings import MEDIA_ROOT, STATIC_ROOT, EMAIL_HOST_USER
from app.cron import BTCPrice
from app.encryptation import encrypt, decrypt



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


def activateEmail(request, token):
  
  try:
    decrypted = decrypt(token)
  except: 
    raise PermissionDenied


  info = json.loads(decrypted)
  if not ('operation' in info and info['operation'] == 'activateUserByEmail'):
    raise PermissionDenied

  user = User.objects.filter(id=info['id'], email=info['email']).first()
  user.is_active = True
  user.save()
  return redirect('/')





def home(request):
  if request.user.is_authenticated():
    if request.user.canVerify:
      message = ''' <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>
            Su cuenta no esta verificada. Para poder realizar una operación es necesario que verifique su cuenta.
            <a href=" '''+ reverse('userVerification') + '''"> 
              <button class="btn btn-default"> 
                Verificar ahora 
              </button>
            </a>'''
      messages.error(request, message, extra_tags="safe alert alert-warning alert-dismissible fade in")
    file = open(os.path.join(MEDIA_ROOT, "BTCPrice.json"), "r")
    prices = json.loads(file.read())
    print(prices)
    return render(request, 'dashboard/dashboard_operator.html', {'prices': prices})
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
          update_session_auth_hash(request, passwordForm.user)
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
  if request.user.canVerify:
    if request.method == 'POST':
      if 'file1' in request.FILES and 'file2' in request.FILES:
        file1 = request.FILES['file1']
        file2 = request.FILES['file2']
        file3 = request.FILES['file3']
        if file1.name.lower().endswith(('.png', '.jpeg', '.jpg')) and file2.name.lower().endswith(('.png', '.jpeg', '.jpg')) and file3.name.lower().endswith(('.png', '.jpeg', '.jpg')):
          request.user.service_image = file1
          request.user.id_front = file2
          request.user.selfie_image = file3

          request.user.save()
          return render(request, 'dashboard/userVerificationConfirmation.html')      
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
      'currency':str(i.id_account.id_currency),
      'name': str(i)
    }

  toAccs = {}
  for i in queryset2:
    toAccs[i.id_account.id] = {
      'currency':str(i.id_account.id_currency),
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
        fromCurrency = fromAccount.id_account.id_currency
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
        file = open(os.path.join(STATIC_ROOT, "countries.json"), "r")
        countries = json.loads(file.read())
        file.close()

        operation.save(countries[fromAccount.id_account.id_bank.country], countries[toAccounts[0][0].id_account.id_bank.country], timezone.now())
        for i in toAccounts:
          OperationGoesTo(operation_code = operation, number_account = i[0].id_account, amount = i[1] ).save()
        
        return render(request, 'dashboard/operationConfirmation.html', {
                        'bank_name': fromAccount.id_account.id_bank.name,
                        'bank_account': 1012366452,
                        'bank_aba': fromAccount.id_account.id_bank.aba,
                        'amount': "%s %s"%(fromCurrency, total),
                        'operationID': operation.code})

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
  if operation.id_client.id != request.user.id:
    raise PermissionDenied
  elif operation.status != "Falta verificacion":
    messages.error(request, 'Esta operación ya fue verificada', extra_tags="alert-error")
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
      currency = form.cleaned_data.get('id_currency')
      if acc.count() == 0:
        acc = Account(number=number,
                      id_bank=bank,
                      id_currency=currency,
                      use_type="Origen" if own else "Destino",
                      is_client=True)
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
  return render(request, 'dashboard/createAccount.html', {"form": form, 'own':own})

def logout(request):
  logout_auth(request)
  return redirect("/")

def login(request):
  if request.user: redirect('/')
  if request.method == 'POST':
    form = AuthenticationForm(request.POST)
    if form.is_valid():
      email = form.cleaned_data.get('email')
      raw_password = form.cleaned_data.get('password1')
      user = authenticate(username=email, password=raw_password)
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
      user.is_active = False
      user.save()
      login_auth(request, user)
      token = {
        'email': email,
        'id': user.id,
        'operation': 'activateUserByEmail'
      }
      token = encrypt(str.encode(json.dumps(token)))
      message = "https://0.0.0.0:8000/activateEmail/" + token
      send_mail(subject="Verificacion de correo electrónico", message=message, from_email=EMAIL_HOST_USER, recipient_list=[email])
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
            actualRate.date = timezone.now()

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
        actualBank = Bank.objects.get(swift=_bank_id)
    except:
        raise Http404

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
        form = EditBankForm(initial={'name': actualBank.name, 'country': actualBank.country, 'swift':_bank_id,
                                      'aba': actualBank.aba})

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
    pass

def adminUser(request):
    pass

def editUser(request):
    pass

def addHoliday(request):
    if (request.method == 'POST'):
        form = NewHolidayForm(request.POST)

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
        form = NewHolidayForm()

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

    if (request.method == 'POST'):
        form = NewHolidayForm(request.POST)

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
                                        'country': actualHoliday.country})

    return render(request, 'admin/editHoliday.html', {'form': form})
