import json
import time
import datetime
import threading
import random

from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404
from django.http import HttpResponseRedirect, HttpResponseServerError
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
from django.db.models import Q
from io import BytesIO
from django.utils import timezone
from django.urls import reverse

from app.forms import *
from app.models import *
from C4H.settings import (MEDIA_ROOT, STATIC_ROOT, EMAIL_HOST_USER,
                          DEFAULT_DOMAIN, DEFAULT_FROM_EMAIL, 
                          OPERATION_TIMEOUT, EMAIL_VALIDATION_EXPIRATION)

from app.encryptation import encrypt, decrypt
import random
from django.db.models import Q, Sum
from decimal import *
from django.core.serializers.json import DjangoJSONEncoder


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


class EmailThread(threading.Thread):
    def __init__(self, subject, message, html_message, recipient_list):
        self.subject = subject
        self.message = message
        self.recipient_list = recipient_list
        self.html_message = html_message
        threading.Thread.__init__(self)

    def run (self):
        send_mail(subject=self.subject,
                  message=self.message,
                  html_message=self.html_message,
                  from_email=DEFAULT_FROM_EMAIL,
                  recipient_list=self.recipient_list)

def activateEmail(request, token):
  '''
    Para activar el email, se debe acceder a un link especial emitido para cada usuario al registrarse,
    que contiene un token encriptado con la informacion necesaria para validar si es el usuario correcto
    Si el token no es valido, se da un error de Permiso denegado.
    El token posee la siguiente informacion:
      - Id del usuario
      - Email asociado al usuario al momento de enviar el correo de validacion
      - Fecha de expiracion del token
      - El tipo de operacion. En este caso "activateUserByEmail"
  '''
  try:
    decrypted = decrypt(token)
  except:
    raise PermissionDenied

  info = json.loads(decrypted)

  if not ('operation' in info and info['operation'] == 'activateUserByEmail'):
    raise PermissionDenied

  expiration = int(info['expiration'])
  now = int(timezone.now().strftime('%s'))
  
  if expiration < now:
    messages.error(request,'Este link expiró. Vuelva a intentarlo enviando un nuevo correo de activación.', extra_tags="alert-warning")
    return redirect(reverse('resendEmailVerification'))
    
  try:
    user = User.objects.get(id=info['id'], email=info['email'])
  except:
    raise PermissionDenied

  if not user.is_active:
    user.is_active = True
    user.save()
    messages.error(request,'Su correo electrónico ha sido validado exitosamente.', extra_tags="alert-success")
    
  return redirect(reverse('login'))




def home(request):
  return render(request, 'index.html')




def checkCurrency(formset, isTarget):
  firstCurrency = None
  # Recorro la primera vez para asegurar que todas las monedas sean iguales
  for form in formset:
    if (form.cleaned_data['selected']):
      try:
        actual_op = Operation.objects.get(code=form.cleaned_data['operation'])
      except:
        return HttpResponseServerError()
      if not(firstCurrency):
        firstCurrency = actual_op.target_currency.code if isTarget else actual_op.origin_currency.code
      elif (firstCurrency != (actual_op.target_currency.code if isTarget else actual_op.origin_currency.code)):
        return False
  return True

@login_required(login_url="/login/")
def closureTransactionModal(request):
  formClosure = ClosureTransactionForm()
  return render(request, 'dashboard/closureTransactionModal.html', {'formClosure':formClosure}) 

def prepareDataOperations(tmpActual, tmpEnded):
  
  actualOperations = []
  endedOperations = []

  for op in tmpActual.iterator():
    tmpSet = set()
    goesTo = op.goesTo.all()
    for g in goesTo.iterator():
      tmpSet.add(g.number_account.id_bank.name)
    actualOperations.append([op, tmpSet])

  for op in tmpEnded.iterator():
    tmpSet = set()
    goesTo = op.goesTo.all()
    for g in goesTo.iterator():
      tmpSet.add(g.number_account.id_bank.name)
    endedOperations.append([op, tmpSet])

  return actualOperations, endedOperations
  
def summaryBanks(request):
  pass

@login_required(login_url="/login/")
def dashboard(request):
  '''
    View del dashboard, tanto para usuarios clientes, como para staff y aliados
    En caso de ser usuario cliente, se redirige al view pendingOperations  
  '''

  # Si es un usuario cliente, deberia entrar en el siguiente condicional
  if not (request.user.has_perm('dashboard.btc_price') or request.user.has_perm('dashboard.operations_operator')):    
    if request.user.canVerify:
      message = ''' <button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>
            Su cuenta no esta verificada. Para poder realizar una operación es necesario que verifique su cuenta.
            <a href=" '''+ reverse('userVerification') + '''"> 
              <button class="btn btn-default"> 
                Verificar ahora 
              </button>
            </a>'''
      messages.error(request, message, extra_tags="safe alert alert-warning alert-dismissible fade in")
    return redirect(reverse('pendingOperations'))
  
  # Si es aliado o staff
  else:
    # Si es usuario tiene el permiso 'operation_all' o admin, puede ver todas las operaciones
    if request.user.has_perm('dashboard.operations_all') or (request.user.is_superuser):
      tmpActOperations = Operation.objects.filter(is_active=True).order_by('-date')
      tmpEndOperations = Operation.objects.filter(is_active=False).order_by('-date')
    # El operador ve todas las operaciones relacionadas con su pais
    elif request.user.groups.filter(name='Operador').exists():
      user = request.user
      operations = Operation.objects.filter(
            Q(id_allie_origin=user) | Q(id_allie_target=user) |
            Q(transactions__origin_account__id_bank__country__name=request.user.country.name) | 
            Q(transactions__target_account__id_bank__country__name=request.user.country.name)
          )
      tmpActOperations = operations.filter(is_active=True).order_by('date')
      tmpEndOperations = operations.filter(is_active=False).order_by('date')
    # El usuario coordinador puede ver sus operaciones y la de sus coordinados
    elif request.user.has_perm('coordinate_operation'):
      ids = request.user.coordinatesUsers.all().values_list('id', flat=True) + [request.user.id]
      tmpActOperations = Operation.objects.filter(
                            Q(is_active=True) & 
                            (Q(id_allie_origin__id__in=ids) | Q(id_allie_target__id__in=ids))
                         ).order_by('date')
      tmpEndOperations = Operation.objects.exclude(status="Cancelada"
                          ).filter( 
                            Q(is_active=False) &
                            (Q(id_allie_origin__id__in=ids) | Q(id_allie_target__id__in=ids))
                          ).order_by('date')
    
    # De otro modo, solo puede ver las operaciones relacionadas a el
    else:
      tmpActOperations = Operation.objects.filter(
                            Q(is_active=True) &
                            (Q(id_allie_origin=request.user) | Q(id_allie_target=request.user))
                          ).order_by('date')
      tmpEndOperations = Operation.objects.exclude(status="Cancelada"
                          ).filter(
                            Q(is_active=False) &
                            (Q(id_allie_origin=request.user) | Q(id_allie_target=request.user))
                          ).order_by('date')

    # Suponemos que no tiene filtro. En caso de que sea POST y contenga el form de un filtre, cambia a True
    hasFilter = False
    # El filtro por default. Esta variable indica en el view, cual de ambas opciones debe colocar "month" o "date" 
    filter = "month" 

    ''' 
      Verificamos si se debe hacer un filtro por mes o por fecha 
    '''
    if request.method == 'POST' and 'filter' in request.POST:
      monthForm = FilterDashboardByMonthForm(request.POST)
      dateForm = FilterDashboardByDateForm(request.POST)
      
      # Si el input 'filter' es 'month', entonces se trata de un filtro por mes
      if request.POST['filter'] == "month" and monthForm.is_valid():
          year = int(request.POST['dateMY_year'])
          month = int(request.POST['dateMY_month'])
          if year and month:
            hasFilter = True
            tmpActOperations = tmpActOperations.filter(date__month=month,date__year=year)
            tmpEndOperations = tmpEndOperations.filter(date__month=month,date__year=year)

            actualOperations, endedOperations = prepareDataOperations(tmpActOperations, tmpEndOperations)
            
      # Por el contrario, si es 'date', entonces es un filtro de fecha
      elif request.POST['filter'] == "date" and dateForm.is_valid():
        date = dateForm.cleaned_data['date']
        # Como el campo date de la operacion es un datetime, hay que tomar solo dia, mes y año
        # ya que toma en cuenta las horas, minutos, etc
        day, month, year = (date.day, date.month, date.year)
        tmpActOperations = tmpActOperations.filter(date__day=day, date__month=month, date__year=year)
        tmpEndOperations = tmpEndOperations.filter(date__day=day, date__month=month, date__year=year)
        hasFilter = True
        filter = "date" # Cambiamos el filtro de "month" a "date"

        actualOperations, endedOperations = prepareDataOperations(tmpActOperations, tmpEndOperations)

    '''
      Si no tiene filtro, entonces colocamos todas las operaciones del mes 
      e inicializamos 2 nuevos forms
    ''' 
    if not hasFilter:
      monthForm = FilterDashboardByMonthForm()
      dateForm = FilterDashboardByDateForm()
      today = timezone.now()
      tmpActOperations = tmpActOperations.filter(date__month=today.month, date__year=today.year)
      tmpEndOperations = tmpEndOperations.filter(date__month=today.month, date__year=today.year)

      actualOperations, endedOperations = prepareDataOperations(tmpActOperations, tmpEndOperations)

    '''
      Cada vez que se piden las operaciones, se actualiza su estado
      A decir verdad, esto deberia estar en un hilo aparte, que se ejecute cada cierto tiempo
      Pero ya que tiene complejidad O(n), no me parecio descabellado
    '''
    for i in tmpActOperations:
      i.isCanceled()


    '''
      Calcular los cuatro indicadores del dashboard
    '''
    # Numero de transacciones bancarias realizadas (Solo las TD)
    nTransactions = 0
    for i in tmpActOperations:
      nTransactions += i.transactions.filter(operation_type="TD").count()
    for i in tmpEndOperations:
      nTransactions += i.transactions.filter(operation_type="TD").count()
    
    # Operaciones pendientes
    totalOpen = tmpActOperations.count()
    # Operaciones terminadas
    totalEnded = tmpEndOperations.count()
    # Operaciones en reclamo
    totalClaim = tmpActOperations.filter(status="En reclamo").count()

    '''
      Pedimos la informacion del archivo static/BTCPrice.json,
      el cual se actualiza con el proceso creado con `$python3 app/cron.py` 
    '''
    file = open(os.path.join(STATIC_ROOT, "BTCPrice.json"), "r")
    prices = json.loads(file.read())
    file.close()

    isAllie = request.user.groups.filter(name='Aliado-1').exists()
    initialForm = [{'operation': op.code, 'selected': False} for op in tmpActOperations.iterator()]

    if (isAllie):
      initialFormEnded = [{'operation': op.code, 'selected': False} for op in tmpEndOperations.iterator()]

    if request.method == 'POST' and not 'filter' in request.POST:
      POST = request.POST.copy()

      auxCount = len(initialForm)
      POST['form-TOTAL_FORMS' ] = auxCount
      POST['form-INITIAL_FORMS'] = auxCount
      POST['form-MAX_NUM_FORMS'] = auxCount

      OperationFormSet = formset_factory(OperationBulkForm, extra=0)
      formset = OperationFormSet(POST)

      if not(isAllie):
        formChoice = StateChangeBulkForm(request.POST)

        if (formChoice.is_valid() and formset.is_valid()):
          new_status = formChoice.cleaned_data['action']
          firstCurrency = None
          totalAmount = Decimal(0)

          #if (new_status == 'Fondos ubicados'):
            #crypto_used = formChoice.cleaned_data['crypto_used']
            #rate = formChoice.cleaned_data['rate']
          #else:
            #banksSummary = {}
          banksSummary = {}

          # Recorro la primera vez para asegurar que todas las monedas sean iguales
          if not(checkCurrency(formset,True)):
            messages.error(request, "Para realizar este cambio de estado debe seleccionar operaciones con la misma moneda destino", extra_tags="alert-warning")
            formChoice = StateChangeBulkForm()
            return render(request, 'dashboard/dashboard_operator.html', {'prices': prices, 'actualO': actualOperations, 'endedO': endedOperations, 'nTransactions': nTransactions, 
                                                                          'totalOpen': totalOpen, 'totalEnded': totalEnded, 'monthForm': monthForm,
                                                                          'dateForm': dateForm, 'filter':filter,
                                                                          'hasFilter': hasFilter, 'form': formset, 'formChoice': formChoice, 'isAllie': False})

          for form in formset:
            if (form.cleaned_data['selected']):
              actual_op = Operation.objects.get(code=form.cleaned_data['operation'])

              if actual_op.status != 'Cancelada' and (canChangeStatusAdmin(actual_op, new_status, request.user.is_superuser) or canChangeStatus(actual_op, new_status)):
                OperationStateChange(operation=actual_op, 
                                     user=request.user,
                                     original_status=actual_op.status).save()
                actual_op.status = new_status

                #  totalAmount += actual_op.fiat_amount*actual_op.exchange_rate

                destiny_banks = OperationGoesTo.objects.filter(operation_code=actual_op.code)
                for b in destiny_banks.iterator():
                  bank = b.number_account.id_bank.name
                  if (bank in banksSummary.keys()):
                    banksSummary[bank] += b.amount*actual_op.exchange_rate
                  else:
                    banksSummary[bank] = b.amount*actual_op.exchange_rate
                actual_op.save()
              else:
                msg = "No se puede cambiar el status a %s" % new_status
                messages.error(request, msg, extra_tags="alert-warning")  
                return render(request, 'dashboard/dashboard_operator.html', { 'prices': prices, 'actualO': actualOperations,'endedO': endedOperations, 'nTransactions': nTransactions, 
                                                                              'totalOpen': totalOpen, 'totalEnded': totalEnded, 'monthForm': monthForm,
                                                                              'dateForm': dateForm, 'filter':filter, 'hasFilter': hasFilter,
                                                                              'form': formset, 'isAllie': False, 'totalClaim': totalClaim, 'formChoice': formChoice})

          messages.error(request, "El cambio de estado se aplicó con éxito", extra_tags="alert-success")
          if (new_status == 'Verificado'):
            return render(request, 'dashboard/summaryBank.html', {'banksSummary': banksSummary})
          return redirect('dashboard')

      else:
        
        formClosure = ClosureTransactionForm(request.POST, request.FILES)

        if (formClosure.is_valid()): #Check the modal
          date = formClosure.cleaned_data['date2']
          transfer_image = request.FILES['transfer_image']
          type_account = formClosure.cleaned_data['type_account']
          exchanger_accepts = formClosure.cleaned_data['exchanger']
          exchanger = exchanger_accepts.exchanger
          currency = exchanger_accepts.currency
          amount = formClosure.cleaned_data['amount']
          transfer_number = formClosure.cleaned_data['transfer_number']

          POST_END = request.POST.copy()

          auxCount = len(initialFormEnded)
          POST_END['form-TOTAL_FORMS' ] = auxCount
          POST_END['form-INITIAL_FORMS'] = auxCount
          POST_END['form-MAX_NUM_FORMS'] = auxCount

          formset_ended = OperationFormSet(POST_END)
         
          if 'pending' in request.POST:
         
            if (formset.is_valid()):
              if not(checkCurrency(formset, False)):
                messages.error(request, "Para realizar esta transacción debe seleccionar operaciones con la misma moneda origen", extra_tags="alert-warning")
                return render(request, 'dashboard/dashboard_operator.html', {'prices': prices, 'actualO': actualOperations,'endedO': endedOperations, 'nTransactions': nTransactions,  
                                                                              'totalOpen': totalOpen, 'totalEnded': totalEnded, 'monthForm': monthForm,
                                                                              'dateForm': dateForm, 'filter':filter,
                                                                              'hasFilter': hasFilter, 'form': formset, 'formEnded': formset_ended,
                                                                              'formClosure': formClosure, 'isAllie': True, 'totalClaim': totalClaim})
              atLeastOne = False
              for form in formset:
                if (form.cleaned_data['selected']):
                  actual_op = Operation.objects.get(code=form.cleaned_data['operation'])
                  if (actual_op.closure.status == 'Activo'):
                    if (actual_op.status != 'Cancelada'):
                      atLeastOne = True
                      origin_account = actual_op.account_allie_origin if type_account=='O' else actual_op.account_allie_target
                      existTransaction = actual_op.transactions.filter(operation_type='TC').exists()
                      if not(existTransaction):
                        new_transaction = Transaction(date=date,
                                                      operation_type="TC",
                                                      transfer_image=transfer_image,
                                                      id_operation=actual_op,
                                                      origin_account=origin_account,
                                                      to_exchanger=exchanger,
                                                      currency=currency,
                                                      amount=actual_op.fiat_amount,
                                                      transfer_number=transfer_number
                                                      ).save()

                      actual_op.ally_pay_back = True
                      actual_op.save()
                  else:
                    messages.error(request, "Algunas de las operaciones seleccionadas se encuentran en cierres de operaciones ya ejecutados", extra_tags="alert-warning")

              if atLeastOne:
                exchanger_accepts.amount_acc += amount
                exchanger_accepts.save()
                messages.error(request, "Las transacciones fueron creadas exitosamente", extra_tags="alert-success")


          elif 'ended' in request.POST:
            
            if (formset_ended.is_valid()):
              if not(checkCurrency(formset_ended, False)):
                messages.error(request, "Para realizar esta transacción debe seleccionar operaciones con la misma moneda origen", extra_tags="alert-warning")
                return render(request, 'dashboard/dashboard_operator.html', {'prices': prices, 'actualO': actualOperations,'endedO': endedOperations, 'nTransactions': nTransactions,  
                                                                              'totalOpen': totalOpen, 'totalEnded': totalEnded, 'monthForm': monthForm,
                                                                              'dateForm': dateForm, 'filter':filter,
                                                                              'hasFilter': hasFilter, 'form': formset, 'formEnded': formset_ended,
                                                                              'formClosure': formClosure, 'isAllie': True, 'totalClaim': totalClaim})

              atLeastOne = False
              for form in formset_ended:
                if (form.cleaned_data['selected']):
                  actual_op = Operation.objects.get(code=form.cleaned_data['operation'])
                  if (actual_op.status != 'Cancelada'):
                    atLeastOne = True
                    origin_account = actual_op.account_allie_origin if type_account=='O' else actual_op.account_allie_target
                    existTransaction = actual_op.transactions.filter(operation_type='TC').exists()
                    if not(existTransaction):
                      new_transaction = Transaction(date=date,
                                                    operation_type="TC",
                                                    transfer_image=transfer_image,
                                                    id_operation=actual_op,
                                                    origin_account=origin_account,
                                                    to_exchanger=exchanger,
                                                    currency=currency,
                                                    amount=actual_op.fiat_amount,
                                                    transfer_number=transfer_number
                                                    ).save()

                    actual_op.ally_pay_back = True
                    actual_op.save()

              if atLeastOne:
                exchanger_accepts.amount_acc += amount
                exchanger_accepts.save()
                messages.error(request, "Las transacciones fueron creadas exitosamente", extra_tags="alert-success")
        
        return redirect('dashboard')

    else:
      OperationFormSet = formset_factory(OperationBulkForm, extra=0)
      formset = OperationFormSet(initial=initialForm)
      if (isAllie):
        formset_ended = OperationFormSet(initial=initialFormEnded)
      formChoice = StateChangeBulkForm()
      actualOperations, endedOperations = prepareDataOperations(tmpActOperations, tmpEndOperations)

    if (isAllie):
      return render(request, 'dashboard/dashboard_operator.html', {'prices': prices, 'actualO': actualOperations,
                                                                    'endedO': endedOperations, 'totalOpen': totalOpen,
                                                                    'totalEnded': totalEnded, 'dateForm': dateForm,'filter':filter,
                                                                    'hasFilter': hasFilter, 'form': formset, 'monthForm': monthForm,
                                                                    'formChoice': formChoice, 'formEnded': formset_ended,
                                                                     'isAllie': True, 'totalClaim': totalClaim, 'nTransactions': nTransactions})

    return render(request, 'dashboard/dashboard_operator.html', {'prices': prices, 'actualO': actualOperations,
                                                                  'endedO': endedOperations, 'nTransactions': nTransactions, 'totalOpen': totalOpen,
                                                                  'totalEnded': totalEnded, 'monthForm': monthForm,
                                                                  'dateForm': dateForm, 'filter':filter,
                                                                  'hasFilter': hasFilter, 'form': formset,
                                                                  'formChoice': formChoice, 'isAllie': isAllie, 'totalClaim': totalClaim})

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
      if 'file1' in request.FILES and 'file2' in request.FILES and 'file3' in request.FILES and 'file4' in request.FILES: 
        file1 = request.FILES['file1']
        file2 = request.FILES['file2']
        file3 = request.FILES['file3']
        file4 = request.FILES['file4']

        # Verificar que todos tienen extension png o jpeg
        ok  = file1.name.lower().endswith(('.png', '.jpeg', '.jpg'))
        ok &= file2.name.lower().endswith(('.png', '.jpeg', '.jpg'))
        ok &= file3.name.lower().endswith(('.png', '.jpeg', '.jpg'))
        ok &= file4.name.lower().endswith(('.png', '.jpeg', '.jpg'))
        
        if ok:
          request.user.service_image = file1
          request.user.id_front = file2
          request.user.id_back = file3
          request.user.selfie_image = file4

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
    messages.error(request, 'Usted no puede realizar envíos de dinero hasta que su cuenta no haya sido verificada.',
                   extra_tags="safe alert alert-warning alert-dismissible fade in")
    return redirect(reverse('dashboard'))


  abt        = AccountBelongsTo.objects.filter(id_client=request.user.id)
  fee        = 0.00 # No se usa en este momento

  rates      = {} #> Estas tres variables se convierten en un json, que despues es
  toAccs     = {} #> utilizado en los javascripts, ya que se busca que sea lo mas 
  fromAccs   = {} #> interactivo posible.
  
  currencies = [] # Se usa para filtrar las cuentas por monedas
  queryset1  = abt.filter(use_type='Origen') # Cuentas origen
  queryset2  = abt.filter(use_type='Destino')  # Cuentas destino
  ToAccountFormSet = formset_factory(ToAccountForm)
  
  '''
    Obtenemos las tasas de cambio
  '''
  for i in ExchangeRate.objects.all():
    rates[str(i)] = i.rate

  '''
    Obtenemos la informacion necesaria de las cuentas origen
  '''
  for i in queryset1:
    fromAccs[i.id] = { 
      'currency':str(i.id_account.id_currency),
      'name': str(i),
      'country': i.id_account.id_bank.country.name
    }

  '''
    Obtenemos la informacion necesaria de las cuentas destino
  '''
  for i in queryset2:
    toAccs[i.id] = {
      'currency':str(i.id_account.id_currency),
      'name': str(i),
    }
    # Se guardan las monedas para luego filtrar por ellas
    currencies.append(i.id_account.id_currency.pk)

  if request.method == 'POST':
    # Debemos copiar el POST para poder modificarlo y agregarle un maximo de 5 campos en multiform
    POST = request.POST.copy() 

    # El form1 pide al usuario, de cual cuenta quiere enviar dinero (Origen)
    form1 = FromAccountForm(request.POST).setQueryset(queryset1)
    form1.fields['currency'].queryset = Currency.objects.filter(currency_type='FIAT', pk__in=currencies).order_by('code')

    # El form2 da chance al usuario de elegir hasta 5 cuentas destino a las cuales enviar dinero
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
      '''
        Verificamos que todos los datos ingreados sean correctos
      '''
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

      fromCurrency = fromAccount.id_account.id_currency
      toCurrency = form1.cleaned_data['currency']
      strInRate = (str(fromCurrency) + "/" + str(toCurrency)) in rates      
      '''
        Apartir de aqui, se hace la busqueda del aliado que se asociara con la nueva operacion
        Primero se buscan aliados asociado al banco origen
        Luego, se intenta viendo los bancos a los cuales "puede enviar" el banco origen
        De no encontrar, se arroja un error.
      '''
      if ok and strInRate:
        rate   = rates[str(fromCurrency) + "/" + str(toCurrency)]
        bank   = fromAccount.id_account.id_bank
        allies = bank.allies.filter(groups__name__in=['Aliado-1'])

        if allies.count() == 0:
          for cst in fromAccount.id_account.id_bank.canSendTo.all():
            allies = cst.target_bank.allies.filter(groups__name__in=['Aliado-1'])
            if allies.count() > 0:
              break
        cst = fromAccount.id_account.id_bank.canSendTo.all().values_list('target_bank', flat=True)
        cst = Bank.objects.filter(Q(pk__in=cst) | Q(pk=fromAccount.id_account.id_bank.pk))
        if allies.count() != 0:

          ally = allies[random.randint(0, allies.count()-1)]
          try:

            belongsTo = ally.hasAccount.filter(use_type='Origen', id_account__id_bank__in=cst)[0]
            account = belongsTo.id_account
          except:
            for ally in allies:
              try:
                #a = ally.hasAccount.filter()
                #b = ally.hasAccount.filter(use_type='Origen')
                belongsTo = ally.hasAccount.filter(use_type='Origen', id_account__id_bank__pk__in=cst)[0]
                account = belongsTo.id_account
              except Exception as e:
                account = None

          # Si el aliado es encontrado, se crea la operacion exitosamente
          if account is not None:
            delta = datetime.timedelta(seconds=GlobalSettings.get().OPERATION_TIMEOUT*60)

            boxClosure = BoxClosure.objects.filter(date__date=timezone.now().date(), ally=ally, currency=fromCurrency)

            if not(boxClosure.exists()):
              boxClosure = BoxClosure(date=timezone.now(),
                                      currency=fromCurrency,
                                      ally=ally,
                                      final_amount=Decimal(0),
                                      status='Activo')
              boxClosure.save()
            elif (boxClosure[0].status == 'Cerrado'):
              boxClosure = BoxClosure.objects.filter(date__date=timezone.now() + timezone.timedelta(days=1), ally=ally, currency=fromCurrency)
              if not(boxClosure.exists()):
                boxClosure = BoxClosure(date=timezone.now() + timezone.timedelta(days=1),
                                        currency=fromCurrency,
                                        ally=ally,
                                        final_amount=Decimal(0),
                                        status='Activo')
                boxClosure.save()
              else:
                boxClosure = boxClosure[0]
            else:
              boxClosure = boxClosure[0]

            operation = Operation(fiat_amount     = total,
                                  crypto_rate     = None,
                                  status          = 'Faltan recaudos',
                                  exchanger       = None,
                                  date            = timezone.now(),
                                  expiration      = timezone.now()+delta,
                                  id_client       = request.user,
                                  id_account      = fromAccount.id_account,
                                  exchange_rate   = rate,
                                  origin_currency = fromCurrency,
                                  target_currency = toCurrency,
                                  id_allie_origin = ally,
                                  account_allie_origin = account,
                                  closure = boxClosure
                                )

            # El metodo _save, es un wrapper que permite crear el codigo de la operacion
            # ya que dentro de la operacion no podemos saber el codigo ISO de los paises involucrados
            # Nota: Solo se toman en cuenta el pais origen y el primer pais destino 
            operation._save( fromAccount.id_account.id_bank.country.iso_code,
                             toAccounts[0][0].id_account.id_bank.country.iso_code,
                             timezone.now()
                            )

            '''
              Se verifica si es un dia feriado en alguno de los paises involucrados
              En caso positivo, se da una advertencia de que la operacion puede tomar 
              mas tiempo que de costumbre.
            '''
            holiday = False
            if Holiday.objects.filter(date=datetime.date.today(), country=fromAccount.id_account.id_bank.country.name).count():
              holiday = True

            for i in toAccounts:
              OperationGoesTo(operation_code = operation, number_account = i[0].id_account, amount = i[1] ).save()
              if Holiday.objects.filter(date=datetime.date.today(), country=i[0].id_account.id_bank.country.name).count():
                holiday = True
            
            if holiday:
              messages.error(request, 'Debido a que hoy es un día feriado en alguno de '
                                      'los paises involucrados en la operación, el proceso '
                                      'de la misma puede presentar demoras.', extra_tags="alert-warning")
            
            '''
              Se envia el correo de confirmacion
            '''
            plain_message = 'Se ha creado una operación para el envio de %s %s desde su cuenta %s'%(fromCurrency, total, fromAccount.id_account) 
            
            message = '''
              Se ha creado exitosamente una operación para el envio de:<br>
              <div align="center">
                <h4><b> %s %s </b><h4>
              </div>
              <br>
              Una vez que haya transferido los fondos desde su cuenta de banco <b>%s</b>,
              deberá subir una imagen del comprobante de la transferencia con la cual nuestro
              equipo podra verificar la operación.
              <br><br> 
              Cuando los fondos hayan caido en las cuentasa las que envió dinero,
              se le avisara por correo electrónico que la operación fue completada.
              <br><br>

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
                        'title':  'Sea ha creado la operación exitosamente.',
                        'url': DEFAULT_DOMAIN,
                    }
                )
            EmailThread(subject        = "Verificación de correo electrónico",
                        message        = plain_message,
                        html_message   = html_message,
                        recipient_list = [request.user.email]).start()

            return redirect('verifyOperation', _operation_id=operation.code)
          else:
            messages.error(request, 'No se pudo crear la operación, ya que no hay '
                                    'aliados disponibles en este momento. Por favor, intente mas tarde.',
                                     extra_tags="alert-error"
                          )  
        else:
          messages.error(request, 'No se pudo crear la operación, ya que no hay aliados disponibles en este momento. Por favor, intente mas tarde.', extra_tags="alert-error")  
      elif not strInRate:
        messages.error(request, 'Lo sentimos, no es posible crear una operacion de %s a %s en este momento.'%(str(fromCurrency),str(toCurrency)), extra_tags="alert-error")
      else:
        messages.error(request, 'No se pudo crear la operación. Revise los datos ingresados.', extra_tags="alert-error")

  else:
    form1 = FromAccountForm().setQueryset(queryset1)
    form1.fields['currency'].queryset = Currency.objects.filter(currency_type='FIAT', pk__in=currencies).order_by('code')
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
                'rate': str(json.dumps(rates, cls=DjangoJSONEncoder)),
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
  admin = request.user.has_perm('admin.cancel_operation')
  try: 
    if admin:
      operation = Operation.objects.get(code=_operation_id)
    else:
      operation = Operation.objects.get(code=_operation_id, id_client=request.user.id)
  except: raise PermissionDenied

  if (admin and not operation.status in ['Cancelada', 'Fondos transferidos']) or operation.status == 'Faltan recaudos':
    operation.status = 'Cancelada'
    operation.is_active = False
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
  elif operation.status != "Faltan recaudos":
    messages.error(request, 'Esta operación ya fue verificada', extra_tags="alert-error")
  elif operation.isCanceled():
    messages.error(request, 'Esta operación fue cancelada o expiró', extra_tags="alert-error")

  elif request.method == 'POST':
    if 'file' in request.FILES:
      file = request.FILES['file']
      if file.name.endswith(('.png', 'jpeg', 'jpg')):
        operation.status = "Por verificar"
        operation.save()
        trans = Transaction(date = timezone.now(),
                            amount = operation.fiat_amount,
                            currency = operation.origin_currency,
                            operation_type = "TO",
                            transfer_image = file,
                            id_operation   = operation,
                            origin_account = operation.id_account,
                            target_account = operation.account_allie_origin )
        trans.save()
        return render(request, 'dashboard/verificationConfirmation.html')      
      else:
        messages.error(request, 'Solo puede subir imagenes PNG y JPG.', extra_tags="alert-error")
    else:
      messages.error(request, 'Por favor suba una imagen.', extra_tags="alert-warning")
  start = time.mktime(operation.date.timetuple())
  end = time.mktime(operation.expiration.timetuple())
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
    form = BankAccountForm(request.POST) if own else BankAccountDestForm(request.POST)
    if request.user.canBuyDollar or not own:
      form.fields['bank'].queryset = Bank.objects.all().order_by('country')
    else:
      form.fields['bank'].queryset = Bank.objects.all().exclude(country="Venezuela").order_by('country')

    if form.is_valid():
      number = form.cleaned_data.get('number')
      bank = form.cleaned_data.get('bank')
      acc = Account.objects.filter(number=number, id_bank=bank)
      currency = form.cleaned_data.get('id_currency')
      router = form.cleaned_data.get('router')
      if bank.country.name == "Estados Unidos":
        if router == "" or len(router) != 9:
          messages.error(request,'El número ABA que ingresó es incorrecto. Introduzca un valor válido.', extra_tags="alert-error")
          return render(request, 'dashboard/createAccount.html', {"form": form, 'own':own})
      else:
        router = ""

      if acc.count() == 0:
        acc = Account(number=number,
                      id_bank=bank,
                      id_currency=currency,
                      aba=router)
      else:
        acc = acc[0]
      if AccountBelongsTo.objects.filter(id_client=request.user.id).filter(id_account=acc.id).count() > 0:
          messages.error(request,'Esta cuenta ya se encuentra asociada', extra_tags="alert-warning")
          return redirect("/account/new?own="+request.GET.get('own'))
      acc.save()

      if own:
        AccountBelongsTo.objects.create(id_client=request.user, 
                                        use_type="Origen" if own else "Destino",
                                        active=True,
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
                                        active=True,
                                        id_number=id_number)
      return redirect('accounts')
    else:
      return render(request, 'dashboard/createAccount.html', {"form": form, 'own':own})
  else:

    form = BankAccountForm() if own else BankAccountDestForm()
    if request.user.canBuyDollar or not own:
      form.fields['bank'].queryset = Bank.objects.all().order_by('country')
    else:
      form.fields['bank'].queryset = Bank.objects.all().exclude(country="Venezuela").order_by('country')
  return render(request, 'dashboard/createAccount.html', {"form": form, 'own':own})

def editAccountDetails(request, pk):
  try:
    acc = AccountBelongsTo.objects.get(pk=pk)
  except Exception as e:
    raise PermissionDenied

  if request.method == "POST":
    form = AccountBelongsToForm(request.POST)
    if form.is_valid():
      acc.owner = form.cleaned_data['owner']
      acc.email = form.cleaned_data['email']
      acc.id_number = form.cleaned_data['id_number']
      acc.alias = form.cleaned_data['alias']
      acc.save()
      messages.error(request, 'Se modificaron los datos exitosamente.')
    else:
      return render(request, 'dashboard/editAccount.html', {"form": form})
  form = AccountBelongsToForm(initial={
      'owner': acc.owner,
      'id_number': acc.id_number,
      'email': acc.email,
      'alias': acc.alias
    })
  return render(request, 'dashboard/editAccount.html', {"form": form})

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
    form = AuthenticationForm(request.POST)

    if form.is_valid():
      email = form.cleaned_data.get('email')
      raw_password = form.cleaned_data.get('password1')
      user = authenticate(username=email, password=raw_password)
    
      if user is not None:
        # if user.is_active:
        login_auth(request, user)
        return redirect(request.POST.get('next',reverse('dashboard')))
    
      else:
        try: user = User.objects.get(email= email)
        except: user = None
    
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
    'operation': 'activateUserByEmail',
    'expiration': (timezone.now()+datetime.timedelta(seconds=GlobalSettings.get().EMAIL_VALIDATION_EXPIRATION*60)).strftime('%s')
  }
  token = encrypt(str.encode(json.dumps(token)))

  link = DEFAULT_DOMAIN+"activateEmail/" + token
  plain_message = 'Para validar tu correo electronico, porfavor ingresa al siguiente correo: ' + link
  
  message = '''
    Gracias por elegirnos<br><br>
    Para poder ingresar al sistema, es necesario que valide su correo electrónico ingresando al siguiente enlace: <br><br>
    <a href="%s"> Validar correo </a>
    <br><br>
    Sinceramente,<br>
    Equipo de soporte de Cash4Home
  '''%(link)

  html_message = loader.render_to_string(
          'registration/base_email.html',
          {
              'message': message,
              'title':  'Bienvenido, ' + user.get_full_name(),
              'url': DEFAULT_DOMAIN,
          }
      )
  EmailThread(subject="Verificación de correo electrónico",
              message=plain_message,
              html_message=html_message,
              recipient_list=[user.email]).start()

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
      client_group = Group.objects.get(name='Cliente') 
      client_group.user_set.add(user)
      login_auth(request, user)
      #sendEmailValidation(user)
      form = AuthenticationForm()
      msg = 'Te hemos enviado un correo de confirmación.'
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

@permission_required('admin.view_currency', login_url='/login/')
def adminCurrencies(request):
    if (request.method == 'GET'):
        allCurrencies = Currency.objects.all().order_by('code')

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

@permission_required('admin.view_rate', login_url='/login/')
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
            ExchangeRateHistory(rate=actualRate.rate,
                                date=actualRate.date,
                                original_rate=actualRate,
                                user=request.user).save()
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

def historyExchangeRate(request, _rate_id):
  try:
    actualRate = ExchangeRate.objects.get(id=_rate_id)
  except:
    raise Http404

  return render(request, 'admin/historyExchangeRate.html', {'rate': actualRate})

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


@permission_required('admin.view_bank', login_url='/login/')
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
      cst = actualBank.canSendTo.all().values_list('target_bank__pk', flat=True)
      form = EditBankForm(instance=actualBank, initial={'can_send':Bank.objects.filter(pk__in=cst)})

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

@permission_required('admin.view_account', login_url='/login/')
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

            if ((actualAccount.number!=number) or (actualAccount.id_bank!=bank)):
              if (Account.objects.filter(number=number,id_bank=bank).exists()):
                  msg = "La cuenta que ingresaste ya existe en ese banco"
                  messages.error(request, msg, extra_tags="alert-warning")
                  return render(request, 'admin/editAccount.html', {'form': form})

            aba = form.cleaned_data['aba']
            if ((bank.country.name == 'Estados Unidos') and not(aba)):
                msg = "Debes ingresar el ABA de la cuenta"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/editAccount.html', {'form': form})

            form.save()
            messages.error(request, "La cuenta fue editada con éxito", extra_tags="alert-success")
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

@permission_required('admin.view_user', login_url='/login/')
def adminUser(request):
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


def sendEmailUserVerification(user):

  plain_message = 'Hemos verificado su cuenta. A partir de ahora podrá realizar operaciones dentro de la plataforma de Cash4Home'
  
  message = '''
    A partir de ahora podras realizar operaciones dentro de la plataforma de Cash4Home y enviar remesas a amigos y familiares.
    <br><br>
    Sinceramente,<br>
    Equipo de soporte de Cash4Home
  '''

  html_message = loader.render_to_string(
          'registration/base_email.html',
          {
              'message': message,
              'title': "¡%s, hemos verificado tu cuenta!"%user.get_short_name(),
              'url': DEFAULT_DOMAIN,
          }
      )
  EmailThread(subject="Tu cuenta ha sido verificada",
              message=plain_message,
              html_message=html_message,
              recipient_list=[user.email]).start()


def verifyUser(request, _user_id):
    try:
        actualUser = User.objects.get(id=_user_id)
    except:
        raise Http404

    if actualUser.verified:
      messages.error(request, "Este usuario ya estaba verificado.", extra_tags="alert-warning")
      return render(request, 'admin/viewUser.html', {'user': actualUser})  
    actualUser.verified = True

    actualUser.save()

    msg = "El usuario se verificó con éxito."
    messages.error(request, msg, extra_tags="alert-success")
    sendEmailUserVerification(actualUser)
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

@permission_required('admin.view_holiday', login_url='/login/')
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
            iso_code = form.cleaned_data['iso_code']

            if (Country.objects.filter(name=name).exists()):
                msg = "Ya existe un país con ese nombre. Ingrese otro"
                messages.error(request, msg, extra_tags="alert-warning")
                return render(request, 'admin/addCountry.html', {'form': form})

            new_country = Country()
            new_country.name = name
            new_country.status = int(status)
            new_country.iso_code = iso_code
            new_country.save()

            msg = "El país fue agregado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewCountryForm()

    return render(request, 'admin/addCountry.html', {'form': form})

@permission_required('admin.view_country', login_url='/login/')
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
            iso_code = form.cleaned_data['iso_code']
            if (name != actualCountry.name):
                if (Country.objects.filter(name=name).exists()):
                    msg = "Ya existe un país con ese nombre. Ingrese otro"
                    messages.error(request, msg, extra_tags="alert-warning")
                    return render(request, 'admin/editCountry.html', {'form': form})

                actualCountry.delete()
                actualCountry = Country()

            actualCountry.name = name
            actualCountry.status = int(status)
            actualCountry.iso_code = iso_code
            actualCountry.save()

            msg = "El país fue editado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewCountryForm(initial={'name': actualCountry.name, 'iso_code': actualCountry.iso_code})

    return render(request, 'admin/editCountry.html', {'form': form})


def canChangeStatus(operation, newStatus):
  if operation.status == 'Faltan recaudos' and newStatus == 'Por verificar':
    operation.status = newStatus
    return True
  if operation.status == 'Por verificar' and newStatus == 'Verificado' and operation.transactions.filter(operation_type='TO').count() > 0:
    operation.status = newStatus
    return True
  if operation.status == 'Verificado' and newStatus == 'Fondos ubicados':
    operation.status = newStatus
    return True
  if operation.status == 'En reclamo' and newStatus == 'Fondos transferidos':
    operation.status = newStatus
    operation.is_active = False
    return True
  allTransactions = Transaction.objects.filter(id_operation=operation, operation_type='TD', currency=operation.target_currency) 
  totalAmount = sum([tx.amount for tx in allTransactions])
  if totalAmount >= operation.fiat_amount * operation.exchange_rate and operation.status == 'Fondos ubicados' and newStatus == 'Fondos transferidos':
    operation.status = newStatus
    operation.is_active = False
    return True
  else:
    return False

def canChangeStatusAdmin(operation, newStatus, is_superuser):
  if not is_superuser:
    return False
  else:
    operation.status = newStatus
    operation.is_active = not newStatus in ['Cancelada', 'Fondos transferidos']
  return True

def sendEmailOperationFinished(operation):
  plain_message = 'La operación <b>%s</b> ha sido finalizada y los fondos han sido transferidos.'%operation.code
  
  message = '''
    La operación <b>%s</b> ha sido finalizada y los fondos han sido transferidos. Para ver los detalles de la operacion entre en el siguiente enlace.
    <br>
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
  '''%(operation.code, DEFAULT_DOMAIN+'operation/pending?operation=' + operation.code)

  html_message = loader.render_to_string(
          'registration/base_email.html',
          {
              'message': message,
              'title': "Su operación ha sido finalizada ",
              'url': DEFAULT_DOMAIN,
          }
      )
  EmailThread(subject="Operación finalizada",
              message=plain_message,
              html_message=html_message,
              recipient_list=[operation.id_client.email]).start()

def claimOperation(request, _operation_id):
  try:
    operation = Operation.objects.get(code=_operation_id)
  except Exception as e: 
    raise PermissionDenied
  user = request.user

  if operation.id_client != request.user or operation.status != "Fondos transferidos":
    raise PermissionDenied

  operation.status = 'En reclamo'
  operation.is_active = True
  operation.save()
  return render(request, 'dashboard/claimConfirmation.html')

def operationDetailDashboard(request, _operation_id):
    try:
      operation = Operation.objects.get(code=_operation_id)
    except Exception as e: 
      raise Http404
    user = request.user

    if not ( user.has_perm('admin.edit_operation') or 
             user.has_perm('admin.cancel_operation') or 
             (operation.id_allie_origin and operation.id_allie_origin.id == user.id) or 
             (operation.id_allie_target and operation.id_allie_target.id == user.id)):
      return redirect(reverse('dashboard'))

    transactions = operation.transactions.all()
    ogt = operation.goesTo.all().order_by('number_account__pk')
    accounts = ogt.values_list('number_account__pk', flat=True)
    abt = AccountBelongsTo.objects.filter(id_client=operation.id_client, id_account__pk__in=accounts).order_by('id_account__pk')

    if request.method == "POST":
      form = ChangeOperationStatusForm(request.POST)
      if form.is_valid():
        status = form.cleaned_data['status']
        original_status = operation.status
        if operation.status != 'Cancelada' and (canChangeStatusAdmin(operation, status, request.user.is_superuser) or canChangeStatus(operation, status)):
          operation.save()
          OperationStateChange(operation=operation, 
                               user=request.user,
                               original_status=original_status,
                               new_status=status).save()
          if status == "Fondos transferidos":
            sendEmailOperationFinished(operation)
        else:
          msg = "No se puede cambiar el status a %s" % status
          messages.error(request, msg, extra_tags="alert-warning")  
          form = ChangeOperationStatusForm(initial={'status':operation.status})
      else:
        form = ChangeOperationStatusForm(initial={'status':operation.status})
    else:
      form = ChangeOperationStatusForm(initial={'status':operation.status})
    return render(request, 'admin/viewOperation.html', {'form':form, 'operation': operation, 'transactions':transactions, 'ogt': list(zip(ogt, abt))})
    
@permission_required('admin.add_transaction', login_url='/login/')
def operationAddTransaction(request, _operation_id):
    try:
      operation = Operation.objects.get(code=_operation_id)
    except Exception as e: 
      raise Http404
    
    if not operation.is_active and operation.status == "Cancelada":
      messages.error(request, "Esta operación fue cancelada.", extra_tags="alert-warning")
      return redirect('operationDetailDashboard', _operation_id=_operation_id)
    
    if request.method == "POST":
      form = TransactionForm(request.POST, request.FILES)
      if form.is_valid():
        if (operation.closure.status == 'Activo'):
          type = form.cleaned_data['operation_type']
          file = request.FILES['transfer_image']

          if type in 'TO':
            Transaction(id_operation   = operation,
                        operation_type = type,
                        transfer_image = file,
                        origin_account = form.cleaned_data['origin_account'],
                        target_account = form.cleaned_data['target_account'],
                        date           = form.cleaned_data['date'],
                        amount         = form.cleaned_data['amount'],
                        currency       = form.cleaned_data['currency']).save() 

          elif type == 'TD':
            crypto_used = form.cleaned_data['crypto_used'].currency
            exchanger = form.cleaned_data['crypto_used'].exchanger
            rate = form.cleaned_data['rate']

            Transaction(id_operation   = operation,
                        operation_type = type,
                        transfer_image = file,
                        origin_account = form.cleaned_data['origin_account'],
                        target_account = form.cleaned_data['target_account'],
                        date           = form.cleaned_data['date'],
                        amount         = form.cleaned_data['amount'],
                        currency       = form.cleaned_data['currency'],
                        crypto_rate    = rate,
                        crypto_used    = crypto_used,
                        exchanger      = exchanger).save() 

            #Falta actualizar el monto en el exchanger

            # Sacamos todas las transacciones destino y sumamos sus montos
            allTransactions = Transaction.objects.filter(id_operation=operation, operation_type='TD', currency=operation.target_currency) 
            totalAmount = sum([tx.amount for tx in allTransactions])
            if totalAmount >= operation.fiat_amount * operation.exchange_rate:
              if operation.status == 'Fondos ubicados' and canChangeStatus(operation, 'Fondos transferidos'):
                operation.save()
                sendEmailOperationFinished(operation)
          
          elif type == 'TC':
            Transaction(id_operation   = operation,
                        operation_type = type,
                        transfer_image = file,
                        to_exchanger   = form.cleaned_data['to_exchanger'],
                        date           = form.cleaned_data['date'],
                        amount         = form.cleaned_data['amount'],
                        currency       = form.cleaned_data['currency']).save()
            
          messages.error(request, 'La transacción ha sido agregada con éxito', extra_tags="alert-success")
        else:
          messages.error(request, 'Ya se realizó el cierre de operaciones de este día, no se pueden agregar transacciones', extra_tags="alert-warning")
      else:
        return render(request, 'admin/addTransaction.html', {'form':form, 'operation':operation})
    form = TransactionForm()
    target_accounts_ids = operation.goesTo.all().values_list('number_account', flat=True)
    form.fields['to_exchanger'].queryset = Exchanger.objects.all()
    form.fields['origin_account'].queryset = Account.objects.filter(belongsTo__id_client=request.user)
    form.fields['target_account'].queryset = Account.objects.filter(pk__in=target_accounts_ids)
    return render(request, 'admin/addTransaction.html', {'form':form, 'operation':operation})


@permission_required('admin.edit_operation', login_url='/login/')
def operationEditDashboard(request, _operation_id):
  try:
    operation = Operation.objects.get(code=_operation_id)
  except Exception as e: 
    raise Http404

  # if not operation.is_active:
  #   raise PermissionDenied

  alliesFrom = User.objects.filter(groups__name='Aliado-1', hasAccount__id_account__id_currency=operation.origin_currency).distinct()
  alliesTo = User.objects.filter(groups__name='Aliado-1', hasAccount__id_account__id_currency=operation.target_currency).distinct()

  accountFrom = {}
  accountTo = {}

  for i in alliesFrom:
    accountFrom[i.id] = []  
    for j in i.hasAccount.filter(id_account__id_currency=operation.origin_currency):
      accountFrom[i.id].append({'id':j.id_account.id, 'number': str(j.id_account)})
  
  for i in alliesTo:
    accountTo[i.id] = []
    for j in i.hasAccount.filter(id_account__id_currency=operation.target_currency):
      accountTo[i.id].append({'id':j.id_account.id, 'number': str(j.id_account)})

  if request.method == "POST":
    form = EditOperationForm(request.POST, instance=operation)
    form.fields['id_allie_origin'].queryset = alliesFrom
    form.fields['id_allie_target'].queryset = alliesTo
    if form.is_valid():
      origin_id = form.cleaned_data['id_allie_origin']
      origin_account = form.cleaned_data['account_allie_origin']
      target_id = form.cleaned_data['id_allie_target']
      target_account = form.cleaned_data['account_allie_target']

      ok = True
      if origin_id is not None:
        if origin_account is None or origin_id.hasAccount.filter(id_account=origin_account).count() == 0:
          ok = False
          messages.error(request, 'El aliado origen o la cuenta origen son incorrectos.', extra_tags="alert-error")
      
      if target_id is not None:
        if target_account is None or target_id.hasAccount.filter(id_account=target_account).count() == 0:
          messages.error(request, 'El aliado destino o la cuenta destino son incorrectos.', extra_tags="alert-error")
          ok = False

      if ok:
        operation.id_allie_origin = origin_id
        operation.account_allie_origin = origin_account
        operation.id_allie_target = target_id
        operation.account_allie_target = target_account
        operation.save()
        messages.error(request, 'La operación se actualizó exitosamente', extra_tags="alert-success")
      else:
        return render(request, 'admin/editOperation.html', 
                      { 'form':form,
                        'operation':operation,
                        'accountFrom':json.dumps(accountFrom),
                        'accountTo':json.dumps(accountTo),
                        'initialFrom': operation.account_allie_origin.id if operation.account_allie_origin else "",
                        'initialTo': operation.account_allie_target.id if operation.account_allie_target else ""
                      }
                    )
    else:
      messages.error(request, 'Hubo un error al actualizar la operación', extra_tags="alert-error")
      return render(request, 'admin/editOperation.html', 
                      { 'form':form,
                        'operation':operation,
                        'accountFrom':json.dumps(accountFrom),
                        'accountTo':json.dumps(accountTo),
                        'initialFrom': operation.account_allie_origin.id if operation.account_allie_origin else "",
                        'initialTo': operation.account_allie_target.id if operation.account_allie_target else ""
                      }
                    )
  
  form = EditOperationForm(instance=operation)   
  form.fields['id_allie_origin'].queryset = alliesFrom
  form.fields['id_allie_target'].queryset = alliesTo
  
  return render(request, 'admin/editOperation.html', 
                  { 'form':form,
                    'operation':operation,
                    'accountFrom':json.dumps(accountFrom),
                    'accountTo':json.dumps(accountTo),
                    'initialFrom': operation.account_allie_origin.id if operation.account_allie_origin else "",
                    'initialTo': operation.account_allie_target.id if operation.account_allie_target else ""
                  }
                )

@permission_required('admin.edit_operation', login_url='/login/')
def operationHistory(request, _operation_id):
  try:
    operation = Operation.objects.get(code=_operation_id)
  except Exception as e: 
    raise Http404

  return render(request, 'admin/historyOperation.html', {'operation': operation, 'history': operation.changeHistory.all()})

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

@permission_required('admin.add_exchanger', login_url='/login/')
def addExchanger(request):
    if (request.method=='POST'):
        form = NewExchangerForm(request.POST)

        if (form.is_valid()):
            name = form.cleaned_data['name']

            if not(Exchanger.objects.filter(name=name).exists()):
              new_exchanger = Exchanger(name=name, is_active=True)
              new_exchanger.save()
            else: 
              new_exchanger = Exchanger.objects.get(name=name)

            currency = form.cleaned_data['currency']
            for c in currency:
              if not(ExchangerAccepts.objects.filter(exchanger=new_exchanger, currency=c).exists()):
                accepts = ExchangerAccepts(exchanger=new_exchanger,
                                           currency=c,
                                           amount_acc=0)
                accepts.save()

            msg = "El exchanger fue agregado con éxito"
            messages.error(request, msg, extra_tags="alert-success")
    else:
        form = NewExchangerForm()

    return render(request, 'admin/addExchanger.html', {'form': form})

@permission_required('admin.view_exchanger', login_url='/login/')
def adminExchanger(request):
    if (request.method=='GET'):
        exchangers = ExchangerAccepts.objects.all()

        return render(request, 'admin/adminExchanger.html', {'exchangers': exchangers})

@permission_required('admin.edit_exchanger', login_url='/login/')
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
                                    'is_active': actual_exchanger.is_active, 'amount': ex_accepts.amount_acc})

    return render(request, 'admin/editExchanger.html', {'form': form})


@permission_required('admin.add_repurchase', login_url='/login/')
def addRepurchaseGeneral(request):
    allCurrencies = Currency.objects.all().order_by('code')
    currenciesC = []
    for c in allCurrencies.iterator():
        tmp = Operation.objects.filter(origin_currency=c).exists()
        if (tmp):
          currenciesC.append((c.code, c.code))

    if (request.method == 'POST'):
        form = SelectCurrencyForm(request.POST, currenciesC=currenciesC)

        if (form.is_valid()):
          currency = form.cleaned_data['currency']

          return redirect('addRepurchase', _currency_id=currency)
    else:
        form = SelectCurrencyForm(currenciesC=currenciesC)
    return render(request, 'admin/addRepurchaseGeneral.html', {'form': form})

@permission_required('admin.add_repurchase', login_url='/login/')
def addRepurchase(request, _currency_id):
    try:
      origin_currency = Currency.objects.get(code=_currency_id)
    except:
      raise Http404

    existing_rep = RepurchaseCameFrom.objects.values_list('id_operation',flat=True)
    available_op = Operation.objects.filter(origin_currency=origin_currency, status="Fondos transferidos").exclude(code__in=existing_rep).values_list('code', 'fiat_amount', 'date', 'id_account__id_bank__name')
    initialForm = [{'operation': op[0], 'amount': op[1], \
                      'date': op[2].strftime("%d/%m/%Y"), 'selected': False, 'bank': op[3]} for op in available_op]

    if (request.method == 'POST'):
        POST = request.POST.copy()

        auxCount = len(initialForm)
        POST['form-TOTAL_FORMS' ] = auxCount
        POST['form-INITIAL_FORMS'] = auxCount
        POST['form-MAX_NUM_FORMS'] = auxCount

        OperationFormSet = formset_factory(NewRepurchaseOpForm, extra=0)
        formset = OperationFormSet(POST, initial=initialForm)
        formRep = NewRepurchaseForm(request.POST)

        if (formset.is_valid() and formRep.is_valid()):
          currency = formRep.cleaned_data['currency'].currency
          exchanger = formRep.cleaned_data['currency'].exchanger
          date = formRep.cleaned_data['date']
          rate = formRep.cleaned_data['rate']

          atLeastOne = False
          firstSelected = True
          new_repurchase = Repurchase(date=date,
                                      rate=rate,
                                      origin_currency=origin_currency,
                                      target_currency=currency,
                                      exchanger=exchanger)
          totalRepurchase = 0
          for form in formset:
              if (form.cleaned_data['selected']):
                atLeastOne = True

                codeOperation = form.cleaned_data['operation']
                operation = Operation.objects.get(code=codeOperation)

                if (firstSelected):
                  new_repurchase.save()
                  firstSelected = False

                totalRepurchase += operation.fiat_amount*Decimal(rate)
                new_cameFrom = RepurchaseCameFrom(id_repurchase=new_repurchase,id_operation=operation)
                new_cameFrom.save()

          if not(atLeastOne):
              msg = "Debes seleccionar al menos una operación"
              messages.error(request, msg, extra_tags="alert-warning")
              return render(request, 'admin/addRepurchase.html', {'formOp': formset, 'formRep': formRep})

          new_repurchase.amount = totalRepurchase
          new_repurchase.save()

          accepts = ExchangerAccepts.objects.get(exchanger=exchanger, currency=currency)
          accepts.amount_acc = accepts.amount_acc + totalRepurchase
          accepts.save()

          msg = "La recompra fue agregada con éxito"
          messages.error(request, msg, extra_tags="alert-success")
          return redirect('adminRepurchase')
        else:
          print(formset.errors)
          print(formRep.errors)
    else:
        OperationFormSet = formset_factory(NewRepurchaseOpForm, extra=0)
        formset = OperationFormSet(initial=initialForm)
        formRep = NewRepurchaseForm()

    return render(request, 'admin/addRepurchase.html', {'formOp': formset, 'formRep': formRep})

@permission_required('admin.view_repurchase', login_url='/login/')
def adminRepurchase(request):
    if (request.method == 'GET'):
      all_repurchases = Repurchase.objects.all()

      return render(request, 'admin/adminRepurchase.html', {'repurchases': all_repurchases})

@permission_required('admin.view_repurchase', login_url='/login/')
def viewRepurchase(request, _repurchase_id):
    try:
        actual_repurchase = Repurchase.objects.get(id=_repurchase_id)
    except:
        raise Http404

    if (request.method == 'GET'):
        came_from = RepurchaseCameFrom.objects.filter(id_repurchase=actual_repurchase)

        return render(request, 'admin/viewRepurchase.html', {'rep': actual_repurchase, 'came_from': came_from})


@permission_required('admin.add_group', login_url='/login/')
def addGroup(request):
  form = GroupForm()

  if request.method == 'POST':
    form = GroupForm(request.POST)
    if form.is_valid():
      form.save()
      messages.error(request, 'El grupo fue agregado con éxito', extra_tags="alert-success")
  return render(request, 'admin/addGroup.html', {'form': form})

@permission_required('admin.view_group', login_url='/login/')
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
      messages.error(request, 'El grupo fue editado con éxito', extra_tags="alert-success")
  return render(request, 'admin/editGroup.html', {'form': form})

@permission_required('admin.edit_settings', login_url='/login/')
def globalSettings(request):
  if request.method == "POST":
    form = GlobalSettingsForm(request.POST, instance=GlobalSettings.get())
    if form.is_valid():
      form.save()
  else:
    form = GlobalSettingsForm(instance=GlobalSettings.get())
  return render(request, 'admin/editSettings.html', {'form': form})

#Faltan permisos
def summaryByAlly(request):
  if (request.method == 'POST'):
    pass
  else:
    allies = User.objects.filter(groups__name='Aliado-1')
    closure_table = {}
    general_received = 0
    general_sent = 0
    for ally in allies.iterator():
      op_involved = Operation.objects.filter(id_allie_origin=ally).exclude(status="Cancelada")
      closures = BoxClosure.objects.filter(ally=ally)

      for c in closures.iterator():
        op_closure = op_involved.filter(closure=c)
        total_received = op_closure.count()
        aux_received = op_closure.aggregate(total_received=Sum('fiat_amount'))
        aux = op_closure.filter(ally_pay_back=True)
        if (aux):
          total_sent = aux.count()
          aux_sent = aux.aggregate(total_sent=Sum('fiat_amount'))
        else:
          total_sent = Decimal(0)
          aux_sent = {}
          aux_sent['total_sent'] = Decimal(0)
        if (total_received == 0):
          diff =  (-1)*aux_sent['total_sent']
        else:
          diff = aux_received['total_received'] - aux_sent['total_sent']
        closure_table[str(ally.id)+c.date.strftime("%d%m%Y")] = [c, aux_received['total_received'], total_received, aux_sent['total_sent'], total_sent, diff]
        general_received += total_received
        general_sent += total_sent

  return render(request, 'admin/summaryByAlly.html', {'closure_table': closure_table, 'general_received': general_received, 'general_sent': general_sent})

#Faltan permisos
def detailClosure(request,_closure_id):
  try:
    closure = BoxClosure.objects.get(id=_closure_id)
  except:
    raise Http404

  operations = closure.box_closure.exclude(status="Cancelada")

  return render(request, 'admin/detailClosure.html', {'closure': closure, 'operations': operations})

#Faltan permisos
def changeStatusClosure(request, _closure_id):
  try:
    closure = BoxClosure.objects.get(id=_closure_id)
  except:
    raise Http404

  if (closure.status == 'Activo'):
    closure.status = 'Cerrado'
  else:
    closure.status = 'Activo'

  closure.save()
  new_change = BoxClosureHistory(closure=closure,
                                 date=timezone.now(),
                                 made_by=request.user,
                                 new_status=closure.status).save()

  messages.error(request,'Se cambió el estado correctamente', extra_tags="alert-success")
  return redirect('summaryByAlly')

#Faltan permisos
def historyClosure(request):

  all_closures = BoxClosureHistory.objects.all()

  return render(request, 'admin/historyClosure.html', {'closures': all_closures})
