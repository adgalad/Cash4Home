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

from app.forms import SignUpForm, AuthenticationForm

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