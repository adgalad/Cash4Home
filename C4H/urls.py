"""C4H URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,handler404, handler500
from django.contrib import admin
from django.contrib.auth import views as auth_views
from app import views



urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    
    # Reset Password
    url(r'^password_reset/$', auth_views.password_reset, name='password_reset'),
    url(r'^password_reset/done/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.password_reset_complete, name='password_reset_complete'),

    #User
    url(r'^user/profile$', views.profile, name='profile'),
    url(r'^operation/new$', views.createOperation, name='createOperation'),
    url(r'^accounts$', views.accounts, name='accounts'),
    url(r'^account/new$', views.createAccount, name='createAccount'),
    url(r'^operation/uploadImage$', views.uploadImage, name='uploadImage'),

    


    url(r'^$', views.home, name='home'),
    url(r'^index$', views.home, name='home'),
    url(r'^index.html', views.home, name='home'),
    url(r'^company$', views.company, name="company"), # Solo por prueba

    url(r'^accounts/profile/$', views.home, name="home"), # Solo por prueba

    #Admin
    url(r'^add/currency/$', views.addCurrencies, name="addCurrencies"),
    url(r'^all/currency/$', views.adminCurrencies, name="adminCurrencies"),
    url(r'^edit/currency/(?P<_currency_id>\w+)', views.editCurrencies, name="editCurrencies"),

    url(r'^add/exchange_rate/$', views.addExchangeRate, name="addExchangeRate"),
    url(r'^all/exchange_rate/$', views.adminExchangeRate, name="adminExchangeRate"),
    url(r'^edit/exchange_rate/(?P<_rate_id>\w+)', views.editExchangeRate, name="editExchangeRate"),
]

handler404 = views.handler404
handler500 = views.handler500