from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout as login_auth

from io import BytesIO
import time

from app.forms import SignUpForm

def home(request):
  return render(request, 'index.html')

def logout(request):
    login_auth(request)
    return render(request, 'index.html')    


def signup(request):
    print(request.method)
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=email, password=raw_password)
            login(request, user)
            print("Exito")
            return redirect('/')
    else:
        form = SignUpForm()
        print("What")
    return render(request, 'registration/signup.html', {'form': form})