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
from django.conf.urls import url,handler404, handler500, handler403
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
    url(r'^user/verification$', views.userVerification, name='userVerification'),
   
    url(r'^activateEmail/(?P<token>.+)$', views.activateEmail, name="activateEmail"),
   
    url(r'^accounts$', views.accounts, name='accounts'),
    url(r'^account/new$', views.createAccount, name='createAccount'),
    
    url(r'^operation/new$', views.createOperation, name='createOperation'),
    url(r'^operation/verify/(?P<_operation_id>.+)$', views.uploadImage, name='verifyOperation'),
    url(r'^operation/pending$', views.pendingOperations, name='pendingOperations'),
    url(r'^operation/(?P<_operation_id>.+)/details$', views.operationModal, name='operationModal'),

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

    url(r'^add/bank/$', views.addBank, name="addBank"),
    url(r'^all/bank/$', views.adminBank, name="adminBank"),
    url(r'^edit/bank/(?P<_bank_id>\w+)', views.editBank, name="editBank"),

    url(r'^add/account/$', views.addAccount, name="addAccount"),
    url(r'^all/account/$', views.adminAccount, name="adminAccount"),
    url(r'^edit/account/(?P<_account_id>\w+)', views.editAccount, name="editAccount"),

    url(r'^add/user/$', views.addUser, name="addUser"),
    url(r'^all/user/$', views.adminUser, name="adminUser"),
    url(r'^edit/user/(?P<_user_id>\w+)', views.editUser, name="editUser"),
    url(r'^view/user/(?P<_user_id>\w+)', views.viewUser, name="viewUser"),

    url(r'^add/holiday/$', views.addHoliday, name="addHoliday"),
    url(r'^all/holiday/$', views.adminHoliday, name="adminHoliday"),
    url(r'^edit/holiday/(?P<_holiday_id>\w+)', views.editHoliday, name="editHoliday"),

    url(r'^add/country/$', views.addCountry, name="addCountry"),
    url(r'^all/country/$', views.adminCountry, name="adminCountry"),
    url(r'^edit/country/(?P<_country_id>[\w\ ]+)', views.editCountry, name="editCountry"),

    #Dashboards
    url(r'^dashboard/operational/$', views.operationalDashboard, name="operationalDashboard"),
    url(r'^dashboard/operational/(?P<_operation_id>\w+)/details$', views.operationDetailDashboard, name="operationDetailDashboard"),
    url(r'^dashboard/operational/(?P<_operation_id>\w+)/edit$', views.operationEditDashboard, name="operationEditDashboard"),
]

handler403 = views.handler403
handler404 = views.handler404
handler403 = views.handler403
handler500 = views.handler500