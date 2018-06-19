from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse, Http404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth import logout as logout_auth
from django.contrib.auth import login as login_auth
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordChangeForm
from django.template import loader
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
import datetime
from C4H.settings import MEDIA_ROOT, STATIC_ROOT, EMAIL_HOST_USER, DEFAULT_DOMAIN, DEFAULT_FROM_EMAIL, OPERATION_TIMEOUT
from app.encryptation import encrypt, decrypt
import random
from django.db.models import Q

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
  messages.error(request,'Su correo electrónico ha sido validado exitosamente.', extra_tags="alert-success")
  return redirect('/login')

def home(request):
  return render(request, 'index.html')

@login_required(login_url="/login/")
def dashboard(request):

  if request.user.canVerify:
      message = ''' <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>
            Su cuenta no esta verificada. Para poder realizar una operación es necesario que verifique su cuenta.
            <a href=" '''+ reverse('userVerification') + '''"> 
              <button class="btn btn-default"> 
                Verificar ahora 
              </button>
            </a>'''
      messages.error(request, message, extra_tags="safe alert alert-warning alert-dismissible fade in")

  print(request.user.groups.filter(name__in=['Operador', 'Aliado-1', 'Aliado-2', 'Aliado-3']))
  if request.user.is_superuser:
    file = open(os.path.join(MEDIA_ROOT, "BTCPrice.json"), "r")
    prices = json.loads(file.read())
    file.close()
    return render(request, 'dashboard/dashboard_operator.html', {'prices': prices})
  elif request.user.groups.filter(name__in=['Operador', 'Aliado-1', 'Aliado-2', 'Aliado-3']):
    return operationalDashboard(request)
  else:
    return pendingOperations(request)


def company(request):
  return render(request, 'company.html')


@login_required(login_url="/login/")
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

@login_required(login_url="/login/")
def userVerification(request):
  if request.user.canVerify:
    if request.method == 'POST':
      print(request.POST)
      if 'file1' in request.FILES and 'file2' in request.FILES and 'file3' in request.FILES: 
        file1 = request.FILES['file1']
        file2 = request.FILES['file2']
        file3 = request.FILES['file3']
        ok  = file1.name.lower().endswith(('.png', '.jpeg', '.jpg'))
        ok &= file2.name.lower().endswith(('.png', '.jpeg', '.jpg'))
        ok &= file3.name.lower().endswith(('.png', '.jpeg', '.jpg'))
        if ok:
          request.user.service_image = file1
          request.user.id_front = file2
          request.user.selfie_image = file3

          request.user.save()
          return render(request, 'dashboard/userVerificationConfirmation.html')      
        else:
          messages.error(request, 'Solo puede subir imágenes PNG y JPG.', extra_tags="alert-error")
      else:
        messages.error(request, 'Por favor suba las imágenes.', extra_tags="alert-error")
    return render(request, 'dashboard/userVerification.html')
  else:
    return redirect(reverse('dashboard'))

@login_required(login_url="/login/")
def createOperation(request):
  if not request.user.verified:
    messages.error(request, 'Usted no puede realizar envios de dinero hasta que su cuenta no haya sido verificada.',
                   extra_tags="safe alert alert-warning alert-dismissible fade in")
    return redirect(reverse('dashboard'))


  abt        = AccountBelongsTo.objects.filter(id_client=request.user.id)
  fee        = 0.00
  rates      = {}
  toAccs     = {}
  fromAccs   = {}
  queryset1  = abt.filter(use_type='Origen') # Cuentas origen
  queryset2  = abt.filter(use_type='Destino') # Cuentas destino
  ToAccountFormSet = formset_factory(ToAccountForm)
  
  for i in ExchangeRate.objects.all():
    rates[str(i)] = i.rate

  for i in queryset1:
    fromAccs[i.id_account.id] = { 
      'currency':str(i.id_account.id_currency),
      'name': str(i)
    }

  for i in queryset2:
    toAccs[i.id_account.id] = {
      'currency':str(i.id_account.id_currency),
      'name': str(i)
    }

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
        rate   = rates[str(fromCurrency) + "/" + str(toCurrency)]
        bank   = fromAccount.id_account.id_bank
        allies = bank.allies.all()

        if allies.count() == 0:
          for bank in fromAccount.id_account.id_bank.acceptBanks:
            allies = bank.allies.all()
            if allies.count() > 0:
              break

        if allies.count() != 0:

          ally = allies[random.randint(0, allies.count()-1)]
          print('++>', ally)
          try:

            belongsTo = ally.hasAccount.filter(use_type='Origen', id_account__id_bank=bank)[0]
            account = belongsTo.id_account
            print('>>', belongsTo, account)
          except:
            for ally in allies:
              print('-->', ally)
              try:
                belongsTo = ally.hasAccount.filter(use_type='Origen', id_account__id_bank=bank)[0]
                account = belongsTo.id_account
                print('**>', belongsTo, account)
              except:
                account = None

          if account is not None:

            operation = Operation(fiat_amount     = total,
                                  crypto_rate     = None,
                                  status          = 'Falta verificacion',
                                  exchanger       = None,
                                  date            = timezone.now(),
                                  date_ending     = timezone.now()+datetime.timedelta(seconds=OPERATION_TIMEOUT*60), # 90 minutos
                                  id_client       = request.user,
                                  id_account      = fromAccount.id_account,
                                  exchange_rate   = rate,
                                  origin_currency = fromCurrency,
                                  target_currency = toCurrency,
                                  id_allie_origin = ally,
                                  account_allie_origin = account,
                                )

            operation._save(fromAccount.id_account.id_bank.country.iso_code, toAccounts[0][0].id_account.id_bank.country.iso_code, timezone.now())

            # Verificar que en alguno de los paises hay un feriado
            holiday = False
            if Holiday.objects.filter(date=datetime.date.today(), country=fromAccount.id_account.id_bank.country.name).count():
              holiday = True

            for i in toAccounts:
              OperationGoesTo(operation_code = operation, number_account = i[0].id_account, amount = i[1] ).save()
              if Holiday.objects.filter(date=datetime.date.today(), country=i[0].id_account.id_bank.country.name).count():
                holiday = True
            
            if holiday:
              print('hola')
              messages.error(request, 'Debido a que hoy es un día feriado en alguno de los paises involucrados en la operación, el proceso de la misma puede presentar demoras.', extra_tags="alert-warning")
              
            plain_message = 'Se ha creado una operación para el envio de %s %s desde su cuenta %s'%(fromCurrency, total, fromAccount.id_account) 
            
            message = '''
              Se ha creado exitosamente una operación para el envio de:<br>
              <div align="center">
                <h4><b> %s %s </b><h4>
              </div>
              <br>
              Una vez que haya transferido los fondos desde su cuenta de banco <b>%s</b>, deberá subir una imagen del comprobante de la transferencia con la cual nuestro equipo podra verificar la operación.<br><br>
              Cuando los fondos hayan caido en las cuentas a las que envió dinero, se le avisara por correo electrónico que la operación fue completada.<br><br>

              <div align="center">
                <a href="%s">
                  <button class="btn btn-primary">
                    Ver detalles de la operación 
                  </button>
                </a>
              </div>

              <br><br>
              Sinceramente,<br>
              Equipo de soporte de Cash4Home
            '''%(fromCurrency, total, fromAccount.id_account, DEFAULT_DOMAIN+'operation/pending?operation=' + operation.code)

            html_message = loader.render_to_string(
                    'registration/base_email.html',
                    {
                        'message': message,
                        'tittle':  'Sea ha creado la operación exitosamente.',
                        'url': DEFAULT_DOMAIN,
                    }
                )
            send_mail(subject        = "Verificación de correo electrónico",
                      message        = plain_message,
                      html_message   = html_message,
                      from_email     = DEFAULT_FROM_EMAIL,
                      recipient_list = [request.user.email])

            return redirect('verifyOperation', _operation_id=operation.code)
          else:
            messages.error(request, 'No se pudo crear la operación, ya que no hay aliados disponibles en este momento. Por favor, intente mas tarde.', extra_tags="alert-error")  
        else:
          messages.error(request, 'No se pudo crear la operación, ya que no hay aliados disponibles en este momento. Por favor, intente mas tarde.', extra_tags="alert-error")  
      else:
        messages.error(request, 'No se pudo crear la operación. Revise los datos ingresados', extra_tags="alert-error")

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

@login_required(login_url="/login/")
def pendingOperations(request):
  operations = Operation.objects.filter(id_client=request.user).exclude(status='Cancelada')
  for i in operations:
    i.isCanceled()
  pending = operations.exclude(status="Fondos transferidos")
  complete = operations.filter(status="Fondos transferidos")
  return render(request, 'dashboard/pendingOperations.html', {'pendingOperations':pending, 'completeOperations':complete}) 

@login_required(login_url="/login/")
def operationModal(request, _operation_id):
  try: operation = Operation.objects.get(code=_operation_id, id_client=request.user.id)
  except: raise PermissionDenied
  ogt = OperationGoesTo.objects.filter(operation_code = operation)
  if operation:
    return render(request, 'dashboard/operationModal.html', {'operation':operation, 'ogt': ogt}) 
  else: 
    return


@login_required(login_url="/login/")
def cancelOperation(request, _operation_id):
  try: operation = Operation.objects.get(code=_operation_id, id_client=request.user.id)
  except: raise PermissionDenied

  if operation.status == 'Falta verificacion':
    operation.status = 'Cancelada'
    operation.save()
    return render(request, 'dashboard/cancelOperation.html', {'operation':operation}) 
  else:
    raise PermissionDenied

@login_required(login_url="/login/")
def verifyOperation(request, _operation_id):
  msg = ""
  
  try: operation = Operation.objects.get(code=_operation_id)
  except: raise Http404
  if operation.id_client.id != request.user.id:
    raise PermissionDenied
  elif operation.status != "Falta verificacion":
    messages.error(request, 'Esta operación ya fue verificada', extra_tags="alert-error")
  elif operation.isCanceled():
    messages.error(request, 'Esta operación fue cancelada o expiró', extra_tags="alert-error")

  elif request.method == 'POST':
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
  start = time.mktime(operation.date.timetuple())
  end = time.mktime(operation.date_ending.timetuple())
  return render(request, 'dashboard/verifyOperation.html', { "operation": operation, 'start':start, 'end':end })  



@login_required(login_url="/login/")
def accounts(request):

  abt = AccountBelongsTo.objects.filter(id_client=request.user.id)
  origin = []
  dest = []
  for i in abt:
    if i.use_type == "Origen":
      origin.append(i)
    else:
      dest.append(i)
  
  return render(request, 'dashboard/accounts.html', {'origin':origin, 'dest':dest})

@login_required(login_url="/login/")
def createAccount(request):
  own = request.GET.get('own')

  if own is None:
    return render(request, 'error_handling/page_404.html')
  own = own == "1"

  if request.method == 'POST':
    form = BankAccountForm(request.POST, canBuyDollar = request.user.canBuyDollar) if own else BankAccountDestForm(request.POST)
    if form.is_valid():
      number = form.cleaned_data.get('number')
      bank = form.cleaned_data.get('bank')
      acc = Account.objects.filter(number=number, id_bank=bank)
      currency = form.cleaned_data.get('id_currency')
      router = form.cleaned_data.get('router')
      if acc.count() == 0:
        acc = Account(number=number,
                      id_bank=bank,
                      id_currency=currency,
                      is_client=True,
                      active=True,
                      aba=router)
      else:
        acc = acc[0]
        acc.is_client = own

      if AccountBelongsTo.objects.filter(id_client=request.user.id).filter(id_account=acc.id).count() > 0:
          messages.error(request,'Esta cuenta ya se encuentra asociada', extra_tags="alert-warning")
          return redirect("/account/new?own="+request.GET.get('own'))
      acc.save()

      if own:
        AccountBelongsTo.objects.create(id_client=request.user, 
                                        use_type="Origen" if own else "Destino",
                                        id_account=acc)
      else:
        email = form.cleaned_data.get('email').lower()
        alias = form.cleaned_data.get('alias')
        owner = form.cleaned_data.get('owner').title()

        id_number = form.cleaned_data.get('id_number')
        AccountBelongsTo.objects.create(id_client=request.user, 
                                        id_account=acc,
                                        use_type="Origen" if own else "Destino",
                                        email=email,
                                        alias=alias,
                                        owner=owner,
                                        id_number=id_number)
             
      return redirect('accounts')
  else:
    form = BankAccountForm(canBuyDollar = request.user.canBuyDollar) if own else BankAccountDestForm()
  return render(request, 'dashboard/createAccount.html', {"form": form, 'own':own})



def password_reset(request):
  if request.method == "POST":
    form = ChangeEmailForm(request.POST)
    if form.is_valid():
      email = form.cleaned_data.get('email')
      try: user = User.objects.get(email=email)
      except: user = None

      if user is None:
        messages.error(request,'El correo que ingresó no se encuentra registrado.', extra_tags="alert-warning")
        return render(request, 'registration/password_reset_form.html', {'form': form})
      elif not user.is_active:
        messages.error(request,'La cuenta asociada a este correo no se encuentra activa.', extra_tags="alert-warning")
        return render(request, 'registration/password_reset_form.html', {'form': form})

  return auth_views.password_reset(request, password_reset_form=MyPasswordResetForm)

def logout(request):
  logout_auth(request)
  return redirect("/")

def login(request):
  if request.user.is_authenticated(): return redirect(reverse('dashboard'))
  if request.method == 'POST':
    print('Hola')
    form = AuthenticationForm(request.POST)
    if form.is_valid():
      print('chao')
      email = form.cleaned_data.get('email')
      raw_password = form.cleaned_data.get('password1')
      user = authenticate(username=email, password=raw_password)
      if user is not None:
        print('Jamon')
        # if user.is_active:
        login_auth(request, user)
        print(request.POST.get('next',reverse('dashboard')))
        return redirect(request.POST.get('next',reverse('dashboard')))
      else:
        user = User.objects.get(email= email)
        if not (user is None or user.is_active):
          msg = 'Debe verificar su correo electronico antes de poder ingresar. <a href="' + reverse('resendEmailVerification') + '">Reenviar correo</a>'
          messages.error(request, msg, extra_tags="safe alert-warning")
        else:
          messages.error(request,'El correo electrónico o la contraseña son inválidos.', extra_tags="alert-error")
    else:
      messages.error(request,'El correo electrónico o la contraseña son inválidos.', extra_tags="alert-error")
    return redirect('login')
  else:
    form = AuthenticationForm()

  return render(request, 'registration/login.html', {'form': form})

def sendEmailValidation(user):
  token = {
    'email': user.email,
    'id': user.id,
    'operation': 'activateUserByEmail'
  }
  token = encrypt(str.encode(json.dumps(token)))

  link = DEFAULT_DOMAIN+"activateEmail/" + token
  plain_message = 'Para validar tu correo electronico, porfavor ingresa al siguiente correo: ' + link
  
  message = '''
    Gracias por elegirnos<br><br>
    Para poder ingresar al sistema, es necesario que valide su correo electrónico ingresando al siguiente enlace: <br><br>
    <a href="%s"> Validar correo </a>
    <br><br><br>
    Sinceramente,<br>
    Equipo de soporte de Cash4Home
  '''%(link)

  html_message = loader.render_to_string(
          'registration/base_email.html',
          {
              'message': message,
              'tittle':  'Bienvenido, ' + user.get_full_name(),
              'url': DEFAULT_DOMAIN,
          }
      )
  send_mail(subject="Verificación de correo electrónico", message=plain_message, html_message=html_message, from_email=DEFAULT_FROM_EMAIL, recipient_list=[user.email])

def resendEmailVerification(request):
  if request.method == 'POST':
    form = ChangeEmailForm(request.POST)
    if form.is_valid():
      email = form.cleaned_data.get('email')
      
      try: user = User.objects.get(email=email)
      except: user = None
      
      if user is None:
        messages.error(request,'El correo electrónico que ingresó es inválido.', extra_tags="alert-warning")
      elif user.is_active:
        messages.error(request,'Este correo electrónico ya se encuentra verificado.', extra_tags="alert-warning")
      else:
        sendEmailValidation(user)
        messages.error(request,'Se envió la validación a su correo electrónico.', extra_tags="alert-success")
        return redirect('/login')

    else:
      messages.error(request,'El correo electrónico que ingresó es inválido.', extra_tags="alert-warning")
  else:
    form = ChangeEmailForm()
  return render(request, 'registration/resendEmailVerification.html', {'form': form})


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
      sendEmailValidation(user)
      form = AuthenticationForm()
      msg = 'Debe verificar su correo electronico antes de poder ingresar. <a href="' + reverse('resendEmailVerification') + '">Reenviar correo</a>'
      messages.error(request, msg, extra_tags="safe alert-warning")
      return render(request, 'registration/login.html', {'form': form})
  else:
    form = SignUpForm()
  return render(request, 'registration/signup.html', {'form': form})


# Admin views
@permission_required('admin.add_currency', login_url='/login/')
def addCurrencies(request):
    if (request.method == 'POST'):
        form = NewCurrencyForm(request.POST)

        if (form.is_valid()):
            code = form.cleaned_data['code']
            name =  form.cleaned_data['name']
            currency_type = form.cleaned_data['currency_type']

            if (Currency.objects.filter(code=code).exists()):
                msg = "La moneda ingresada ya existe. Elija otro nombre"
                messages.error(request,msg, extra_tags="alert-warning")
                return render(request, 'admin/addCurrency.html', {'form': form})

            new_currency = Currency()
            new_currency.code = code
            new_currency.name = name
            new_currency.currency_type = currency_type

            new_currency.save()

            msg = "La moneda fue agregada con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewCurrencyForm()

    return render(request, 'admin/addCurrency.html', {'form': form})

@permission_required('admin.edit_currency', login_url='/login/')
def adminCurrencies(request):
    if (request.method == 'GET'):
        allCurrencies = Currency.objects.all()

        return render(request, 'admin/adminCurrency.html', {'currencies': allCurrencies})

@permission_required('admin.edit_currency', login_url='/login/')
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
                msg = "El nombre de la moneda ingresado ya existe. Intente con uno diferente"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/editCurrency.html', {'form': form})

            c.name = name
            c.currency_type = form.cleaned_data['currency_type']
            c.save()

            msg = "La moneda se editó con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:    
        form = EditCurrencyForm(initial={'code': c.code, 'name': c.name, 'currency_type': c.currency_type})

    return render(request, 'admin/editCurrency.html', {'form': form})

@permission_required('admin.add_rate', login_url='/login/')
def addExchangeRate(request):

    if (request.method == 'POST'):
        form = NewExchangeRateForm(request.POST)

        if (form.is_valid()):
            rate = form.cleaned_data['rate']
            origin =  form.cleaned_data['origin_currency']
            target = form.cleaned_data['target_currency']

            alreadyExists = ExchangeRate.objects.filter(origin_currency=origin, target_currency=target).exists()

            if (alreadyExists):
                msg = "La tasa de cambio ingresada ya existe. Elija otras monedas"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addExchangeRate.html', {'form': form})

            if (origin == target):
                msg = "Las monedas no pueden ser iguales. Elija otras monedas"
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
        form = NewExchangeRateForm()

    return render(request, 'admin/addExchangeRate.html', {'form': form})

@permission_required('admin.edit_rate', login_url='/login/')
def adminExchangeRate(request):
    if (request.method == 'GET'):
        allRates = ExchangeRate.objects.all()

        return render(request, 'admin/adminExchangeRate.html', {'rates': allRates})

@permission_required('admin.edit_rate', login_url='/login/')
def editExchangeRate(request, _rate_id):
    try:
        actualRate = ExchangeRate.objects.get(id=_rate_id)
    except:
        raise Http404

    if (request.method == 'POST'):
        form = NewExchangeRateForm(request.POST)

        if (form.is_valid()):
            rate = form.cleaned_data['rate']
            origin =  form.cleaned_data['origin_currency']
            target = form.cleaned_data['target_currency']

            if ((origin != actualRate.origin_currency) or (target != actualRate.target_currency)):
                alreadyExists = ExchangeRate.objects.filter(origin_currency=origin, target_currency=target).exists()

                if (alreadyExists):
                    msg = "La tasa de cambio ingresada ya existe. Elija otras monedas"
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editExchangeRate.html', {'form': form})

                if (origin == target):
                    msg = "Las monedas no pueden ser iguales. Elija otras monedas"
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
        form = NewExchangeRateForm(initial={'rate':actualRate.rate, 'origin_currency': actualRate.origin_currency.code, 
                                                'target_currency': actualRate.target_currency.code})

    return render(request, 'admin/editExchangeRate.html', {'form': form})

@permission_required('admin.add_bank', login_url='/login/')
def addBank(request):
    if (request.method == 'POST'):
        form = NewBankForm(request.POST)

        if (form.is_valid()):
            name = form.cleaned_data['name']
            country = form.cleaned_data['country']
            swift = form.cleaned_data['swift']

            if (Bank.objects.filter(swift=swift).exists()):
                msg = "El SWIFT ingresado corresponde a otro banco. Ingrese un SWIFT correcto"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addBank.html', {'form': form})

            new_bank = Bank()
            new_bank.name = name.upper()
            new_bank.country = country
            new_bank.swift = swift
            new_bank.save()

            for b in form.cleaned_data['can_send']:
                new_can_send = CanSendTo()
                new_can_send.origin_bank = new_bank
                new_can_send.target_bank = b
                new_can_send.save()

            msg = "El banco fue agregado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:

      form = NewBankForm()

    return render(request, 'admin/addBank.html', {'form': form})


@permission_required('admin.edit_bank', login_url='/login/')
def adminBank(request):
    if (request.method == 'GET'):
        tmp_banks = Bank.objects.all()
        all_banks = []
        for b in tmp_banks:
            tmp_send = CanSendTo.objects.filter(origin_bank=b)
            can_send = ""
            for tmp in tmp_send:
                can_send += tmp.target_bank.name+'-'+tmp.target_bank.country.name+","

            info = {'name': b.name, 'swift': b.swift, 'country': b.country, 'can_send': can_send}
            all_banks.append(info)


        return render(request, 'admin/adminBank.html', {'banks': all_banks})

@permission_required('admin.edit_bank', login_url='/login/')
def editBank(request, _bank_id):
    try:
        actualBank = Bank.objects.get(swift=_bank_id)
    except:
        raise Http404

    if (request.method == 'POST'):
        form = EditBankForm(request.POST, instance=actualBank)

        if (form.is_valid()):
            print(form.cleaned_data['allies'])
            actualBank.allies.clear()
            for i in form.cleaned_data['allies']:
              actualBank.allies.add(i)
            country = form.cleaned_data['country']
            name = form.cleaned_data['name']

            actualBank.country = country
            actualBank.name = name.title()
            actualBank.save()

            CanSendTo.objects.filter(origin_bank=actualBank).delete()

            for b in form.cleaned_data['can_send']:
                new_can_send = CanSendTo()
                new_can_send.origin_bank = actualBank
                new_can_send.target_bank = b
                new_can_send.save()

            msg = "El banco fue editado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
            all_banks = Bank.objects.all()
            return render(request, 'admin/editBank.html', {'form': form})
    else:
        form = EditBankForm(instance=actualBank)

    return render(request, 'admin/editBank.html', {'form': form})

@permission_required('admin.add_account', login_url='/login/')
def addAccount(request):
    if (request.method == 'POST'):
        form = NewAccountForm(request.POST)

        if (form.is_valid()):
            number = form.cleaned_data['number']
            bank = form.cleaned_data['id_bank']

            if (Account.objects.filter(number=number,id_bank=bank).exists()):
                msg = "La cuenta que ingresaste ya existe en ese banco"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addAccount.html', {'form': form})

            aba = form.cleaned_data['aba']
            if ((bank.country.name == 'Estados Unidos') and not(aba)):
                msg = "Debes ingresar el ABA de la cuenta para poder añadirla"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addAccount.html', {'form': form})

            form.save()               

            msg = "La cuenta fue agregada con éxito"
            messages.error(request, msg, extra_tags="alert-success")

    else:
        form = NewAccountForm()

    return render(request, 'admin/addAccount.html', {'form': form})

@permission_required('admin.edit_account', login_url='/login/')
def adminAccount(request):
    if (request.method == 'GET'):
        all_accounts = Account.objects.all()

        return render(request, 'admin/adminAccount.html', {'accounts': all_accounts})

@permission_required('admin.edit_account', login_url='/login/')
def editAccount(request, _account_id):
    try:
        actualAccount = Account.objects.get(id=_account_id)
    except:
        raise Http404

    if (request.method == 'POST'):
        form = NewAccountForm(request.POST, instance=actualAccount)
        if (form.is_valid()):
            number = form.cleaned_data['number']
            bank = form.cleaned_data['id_bank']

            if (Account.objects.filter(number=number,bank=bank).exists()):
                msg = "La cuenta que ingresaste ya existe en ese banco"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/editAccount.html', {'form': form})

            aba = form.cleaned_data['aba']
            if ((bank.country.name == 'Estados Unidos') and not(aba)):
                msg = "Debes ingresar el ABA de la cuenta"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/editAccount.html', {'form': form})

            form.save()
    else:
        form = NewAccountForm(initial={'number': actualAccount.number, 'id_bank': actualAccount.id_bank,
                                        'currency': actualAccount.id_currency, 'aba': actualAccount.aba},
                              instance=actualAccount)

    return render(request, 'admin/editAccount.html', {'form': form})

@permission_required('admin.add_user', login_url='/login/')
def addUser(request):

    if (request.method == 'POST'):
        form = NewUserForm(request.POST)

        if (form.is_valid()):
            new_mail = form.clean_email()
            if (User.objects.filter(email=new_mail).exists()):
                msg = "Ya existe un usuario con el correo ingresado"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addUser.html', {'form': form})

            new_id = form.cleaned_data['id_number']
            new_country = form.cleaned_data['country']
            if (User.objects.filter(id_number=new_id, country=new_country).exists()):
                msg = "El número de identificación pertenece a otra persona"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addUser.html', {'form': form})

            form.save()

            msg = "El usuario fue agregado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewUserForm()

    return render(request, 'admin/addUser.html', {'form': form})

@permission_required('admin.edit_user', login_url='/login/')
def adminUser(request):
    print(request.user.has_perm('admin.edit_user'))
    if (request.method == 'GET'):
        all_clients = User.objects.filter(groups__name__in=['Cliente'])
        all_users = User.objects.exclude(groups__name__in=['Cliente'])
        totalPending = all_clients.filter(verified=False).count()
        totalVerified = all_clients.filter(verified=True).count()
        return render(request, 'admin/adminUser.html', {'clients': all_clients, 'users': all_users, 
                        'totalPending': totalPending, 'totalVerified': totalVerified})


def editUser(request, _user_id):
    try:
        actualUser = User.objects.get(id=_user_id)
    except:
        raise Http404
    
    if (request.method == 'POST'):
        form = NewUserForm(request.POST, instance=actualUser)

        if (form.is_valid()):    
            new_mail = form.clean_email()
            if (new_mail != actualUser.email):
                if (User.objects.filter(email=new_mail).exists()):
                    msg = "Ya existe un usuario con el correo ingresado"
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editUser.html', {'form': form})

            new_id = form.cleaned_data['id_number']
            new_country = form.cleaned_data['country']
            if (new_id != actualUser.id_number):
                if (User.objects.filter(id_number=new_id, country=new_country).exists()):
                    msg = "El número de identificación pertenece a otra persona"
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editUser.html', {'form': form})

            form.save()

            msg = "El usuario fue editado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewUserForm(instance=actualUser)

    return render(request, 'admin/editUser.html', {'form': form})

def viewUser(request, _user_id):
    try:
        actualUser = User.objects.get(id=_user_id)
    except:
        raise Http404

    return render(request, 'admin/viewUser.html', {'user': actualUser})

def verifyUser(request, _user_id):
    try:
        actualUser = User.objects.get(id=_user_id)
    except:
        raise Http404

    actualUser.verified = True

    actualUser.save()

    msg = "El usuario se verificó con éxito"
    messages.error(request, msg, extra_tags="alert-success")
    return render(request, 'admin/viewUser.html', {'user': actualUser})


@permission_required('admin.add_holiday', login_url='/login/')
def addHoliday(request):
    if (request.method == 'POST'):
        form = NewHolidayForm(request.POST)

        if (form.is_valid()):
            date = form.cleaned_data['date']
            description = form.cleaned_data['description']
            country = form.cleaned_data['country']

            if (Holiday.objects.filter(date=date, country=country).exists()):
                msg = "Ya existe un feriado para ese día en " + country.name
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addHoliday.html', {'form': form})

            new_holiday = Holiday()
            new_holiday.date = date
            new_holiday.description = description
            new_holiday.country = country
            new_holiday.save()

            msg = "El feriado fue agregado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewHolidayForm()

    return render(request, 'admin/addHoliday.html', {'form': form})

@permission_required('admin.edit_holiday', login_url='/login/')
def adminHoliday(request):
    if (request.method == 'GET'):
        holidays = Holiday.objects.all()

        return render(request, 'admin/adminHoliday.html', {'holidays': holidays})

@permission_required('admin.edit_holiday', login_url='/login/')
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
                    msg = "Ya existe un feriado para ese día en " + country.name
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editHoliday.html', {'form': form})        

            actualHoliday.date = date
            actualHoliday.description = description
            actualHoliday.country = country

            actualHoliday.save()

            msg = "El feriado fue editado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewHolidayForm(initial={'date': actualHoliday.date, 'description': actualHoliday.description,
                                        'country': actualHoliday.country})

    return render(request, 'admin/editHoliday.html', {'form': form})

@permission_required('admin.add_country', login_url='/login/')
def addCountry(request):
    if (request.method == 'POST'):
        form = NewCountryForm(request.POST)

        if (form.is_valid()):
            name = form.cleaned_data['name']
            status = form.cleaned_data['status']

            if (Country.objects.filter(name=name).exists()):
                msg = "Ya existe un país con ese nombre. Ingrese otro"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addCountry.html', {'form': form})

            new_country = Country()
            new_country.name = name
            new_country.status = int(status)
            new_country.save()

            msg = "El país fue agregado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewCountryForm()

    return render(request, 'admin/addCountry.html', {'form': form})

@permission_required('admin.edit_country', login_url='/login/')
def adminCountry(request):
    if (request.method == 'GET'):
        all_countries = Country.objects.all()

        return render(request, 'admin/adminCountry.html', {'countries': all_countries})

@permission_required('admin.edit_country', login_url='/login/')
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
            actualCountry.save()

            msg = "El país fue editado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewCountryForm(initial={'name': actualCountry.name})

    return render(request, 'admin/editCountry.html', {'form': form})

def operationalDashboard(request):
    if (request.method == 'GET'):
        if request.user.groups.filter(name = 'Operador') or (request.user.is_superuser):
            actualOperations = Operation.objects.filter(is_active=True).order_by('date')
            endedOperations = Operation.objects.filter(is_active=False).order_by('date')
            
        elif request.user.groups.filter(name = 'Aliado-1'):
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

def viewUserAccounts(request, _user_id):
    try:
        user = User.objects.get(id=_user_id)
    except:
        raise Http404

    ownAccounts = AccountBelongsTo.objects.filter(id_client=user, use_type='Origen')
    thirdAccounts = None
    if (user.user_type == 'Cliente'):
        thirdAccounts = AccountBelongsTo.objects.filter(id_client=user, use_type='Destino')

    return render(request, 'admin/viewUserAccounts.html', {'origin': ownAccounts, 'dest': thirdAccounts, 'u': user})

def deactivateUserAccount(request, _user_id, _account_id):
    try:
        user = User.objects.get(id=_user_id)
        account = Account.objects.get(id=_account_id)
        belongs_to = AccountBelongsTo.objects.get(id_client=user, id_account=account)
    except:
        raise Http404

    belongs_to.active = not(belongs_to.active)
    belongs_to.save()

    if (belongs_to.active):
        msg = "La cuenta se activó con éxito"
    else:
        msg = "La cuenta se desactivó con éxito"
    messages.error(request, msg, extra_tags="alert-success")
    ownAccounts = AccountBelongsTo.objects.filter(id_client=user, use_type='Origen')
    thirdAccounts = None
    if (user.user_type == 'Cliente'):
        thirdAccounts = AccountBelongsTo.objects.filter(id_client=user, use_type='Destino')
    
    return render(request, 'admin/viewUserAccounts.html', {'origin': ownAccounts, 'dest': thirdAccounts, 'u': user})


def addUserAccount(request, _user_id, _flag):
    try:
        user = User.objects.get(id=_user_id)
    except:
        raise Http404

    if (request.method == 'POST'):
        if (_flag == 'own'):
            form = NewOwnAccountAssociatedForm(request.POST)
        else:
            form = NewThirdAccountAssociatedForm(request.POST)

        if (form.is_valid()):
            account = form.cleaned_data['account']

            if (AccountBelongsTo.objects.filter(id_client=user, id_account=account).exists()):
                msg = "La cuenta seleccionada ya está asociada a este usuario"
                messages.error(request, msg, extra_tags="alert-warning")            
                return render(request, 'admin/addUserAccount.html', {'form': form, 'u': user})

            belongs_to = AccountBelongsTo()
            belongs_to.id_account = account
            belongs_to.id_client = user

            if (_flag == 'thirds'):
                belongs_to.owner = form.cleaned_data['owner']
                belongs_to.alias = form.cleaned_data['alias']
                belongs_to.email = form.cleaned_data['email']
                belongs_to.id_number = form.cleaned_data['id_number']
                belongs_to.use_type = 'Destino'
            else:
                belongs_to.use_type = form.cleaned_data['use_type']

            belongs_to.save()

            msg = "La cuenta fue asociada exitosamente"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        if (_flag == 'own'):
            form = NewOwnAccountAssociatedForm()
        else:
            form = NewThirdAccountAssociatedForm()

    return render(request, 'admin/addUserAccount.html', {'form': form, 'u': user})

def addExchanger(request):
    if (request.method=='POST'):
        form = NewExchangerForm(request.POST)

        if (form.is_valid()):
            name = form.cleaned_data['name']

            if (Exchanger.objects.filter(name=name).exists()):
                msg = "El nombre ingresado ya existe en el sistema"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addExchanger.html', {'form': form})

            new_exchanger = Exchanger(name=name, is_active=True)
            new_exchanger.save()

            currency = form.cleaned_data['currency']
            for c in currency:
                accepts = ExchangerAccepts(exchanger=new_exchanger,
                                           currency=c,
                                           amount_acc=0)
                accepts.save()

            msg = "El exchanger fue agregado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewExchangerForm()

    return render(request, 'admin/addExchanger.html', {'form': form})

def adminExchanger(request):
    if (request.method=='GET'):
        exchangers = ExchangerAccepts.objects.all()

        return render(request, 'admin/adminExchanger.html', {'exchangers': exchangers})

def editExchanger(request, _ex_id, _currency_id):
    try:
        actual_exchanger = Exchanger.objects.get(name=_ex_id)
        currency = Currency.objects.get(code=_currency_id)
        ex_accepts = ExchangerAccepts.objects.get(exchanger=actual_exchanger, currency=currency)
    except:
        raise Http404

    if (request.method=='POST'):
        form = EditExchangerForm(request.POST)

        if (form.is_valid()):
            actual_exchanger.is_active = form.cleaned_data['is_active']
            actual_exchanger.save()
            ex_accepts.amount_acc = form.cleaned_data['amount']
            ex_accepts.save()

            msg = "El exchanger fue editado exitosamente"
            messages.error(request, msg, extra_tags="alert-success")

    else:
        form = EditExchangerForm(initial={'name': actual_exchanger.name, 'currency': currency.name,
                                    'is_active': actual_exchanger.is_active})

    return render(request, 'admin/editExchanger.html', {'form': form})

def addRepurchase(request):
    pass

def adminRepurchase(request):
    pass

def editRepurchase(request, _rep_id):
    pass

@permission_required('admin.add_group', login_url='/login/')
def addGroup(request):
  form = GroupForm()

  if request.method == 'POST':
    form = GroupForm(request.POST)
    if form.is_valid():
      form.save()
      messages.error(request, 'El grupo fue agregado con exito', extra_tags="alert-success")
  return render(request, 'admin/addGroup.html', {'form': form})

@permission_required('admin.edit_group', login_url='/login/')
def adminGroup(request):
    if (request.method == 'GET'):
        all_groups = Group.objects.all()
        return render(request, 'admin/adminGroup.html', {'groups': all_groups})

@permission_required('admin.edit_group', login_url='/login/')
def editGroup(request, _group_id):
  try:
    actualGroup = Group.objects.get(id=_group_id)
  except:
    raise Http404
  
  form = GroupForm(instance=actualGroup)

  if request.method == 'POST':
    form = GroupForm(request.POST, instance=actualGroup)
    if form.is_valid():
      form.save()
      messages.error(request, 'El grupo fue editado con exito', extra_tags="alert-success")
  return render(request, 'admin/editGroup.html', {'form': form})



# Me parece q crear permiso no sirve de mucho, ya que hay q tocar codigo o crear un mecanismo dinamico que asigne el permiso a una view.

# def addPermission(request):
#   form = PermissionForm()
#   if request.method == 'POST':
#     form = PermissionForm(request.POST)
#     if form.is_valid():
#       form.save()
#       messages.error(request, 'El permiso fue agregado con exito', extra_tags="alert-success")
#   return render(request, 'admin/addPermission.html', {'form': form})