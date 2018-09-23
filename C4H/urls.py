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
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static

from app import views
from C4H.settings import MEDIA_URL, MEDIA_ROOT, STATIC_URL, STATIC_ROOT

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^app/signup/$', views.signup, name='signup'),
    url(r'^app/login/$', views.login, name='login'),
    url(r'^app/logout/$', views.logout, name='logout'),

    # Reset Password
    url(r'^app/password_reset/$', views.password_reset, name='password_reset'),
    url(r'^app/password_reset/done/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^app/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        name='password_reset_confirm'
       ),
    url(r'^app/reset/done/$', auth_views.password_reset_complete, name='password_reset_complete'),

    #User
    url(r'^app/dashboard$', views.dashboard, name='dashboard'),
    url(r'^app/dashboard/closure$', views.closureTransactionModal, name='closureTransactionModal'),
    url(r'^app/user/profile$', views.profile, name='profile'),
    url(r'^app/user/verification$', views.userVerification, name='userVerification'),

    url(r'^app/emailVerification$', views.resendEmailVerification, name="resendEmailVerification"),
    url(r'^app/activateEmail/(?P<token>.+)$', views.activateEmail, name="activateEmail"),

    url(r'^app/accounts$', views.accounts, name='accounts'),
    url(r'^app/account/new$', views.createAccount, name='createAccount'),
    url(r'^app/account/edit/(?P<pk>.+)$', views.editAccountDetails, name='editAccountDetails'),

    url(r'^app/operation/new$', views.createOperation, name='createOperation'),
    url(r'^app/operation/verify/(?P<_operation_id>.+)$', views.verifyOperation, name='verifyOperation'),
    url(r'^app/operation/pending$', views.pendingOperations, name='pendingOperations'),
    url(r'^app/operation/(?P<_operation_id>.+)/details$', views.operationModal, name='operationModal'),
    url(r'^app/operation/(?P<_operation_id>.+)/cancel$', views.cancelOperation, name='cancelOperation'),
    url(r'^app/operation/(?P<_operation_id>.+)/claim$', views.claimOperation, name='claimOperation'),

    url(r'^app/$', views.home, name='home'),
    url(r'^app/index$', views.home, name='home'),
    url(r'^app/index.html', views.home, name='home'),
    url(r'^app/company$', views.company, name="company"), # Solo por prueba

    url(r'^app/accounts/profile/$', views.home, name="home"), # Solo por prueba

    #Admin
    url(r'^app/add/currency/$', views.addCurrencies, name="addCurrencies"),
    url(r'^app/all/currency/$', views.adminCurrencies, name="adminCurrencies"),
    url(r'^app/edit/currency/(?P<_currency_id>\w+)', views.editCurrencies, name="editCurrencies"),

    url(r'^app/add/exchange_rate/$', views.addExchangeRate, name="addExchangeRate"),
    url(r'^app/all/exchange_rate/$', views.adminExchangeRate, name="adminExchangeRate"),
    url(r'^app/edit/exchange_rate/(?P<_rate_id>\w+)', views.editExchangeRate, name="editExchangeRate"),
    url(r'^app/all/exchange_rate/(?P<_rate_id>\w+)', views.historyExchangeRate, name="historyExchangeRate"),

    url(r'^app/add/bank/$', views.addBank, name="addBank"),
    url(r'^app/all/bank/$', views.adminBank, name="adminBank"),
    url(r'^app/edit/bank/(?P<_bank_id>\w+)', views.editBank, name="editBank"),

    url(r'^app/add/account/$', views.addAccount, name="addAccount"),
    url(r'^app/all/account/$', views.adminAccount, name="adminAccount"),
    url(r'^app/edit/account/(?P<_account_id>\w+)', views.editAccount, name="editAccount"),

    url(r'^app/add/user/$', views.addUser, name="addUser"),
    url(r'^app/all/user/$', views.adminUser, name="adminUser"),
    url(r'^app/edit/user/(?P<_user_id>\w+)', views.editUser, name="editUser"),
    url(r'^app/view/user/(?P<_user_id>\w+)', views.viewUser, name="viewUser"),
    url(r'^app/verify/user/(?P<_user_id>\w+)', views.verifyUser, name="verifyUser"),

    url(r'^app/add/holiday/$', views.addHoliday, name="addHoliday"),
    url(r'^app/all/holiday/$', views.adminHoliday, name="adminHoliday"),
    url(r'^app/edit/holiday/(?P<_holiday_id>\w+)', views.editHoliday, name="editHoliday"),

    url(r'^app/add/country/$', views.addCountry, name="addCountry"),
    url(r'^app/all/country/$', views.adminCountry, name="adminCountry"),
    url(r'^app/edit/country/(?P<_country_id>[\w\ ]+)', views.editCountry, name="editCountry"),

    url(r'^app/add/group$', views.addGroup, name="addGroup"),
    url(r'^app/all/group/$', views.adminGroup, name="adminGroup"),
    url(r'^app/edit/group/(?P<_group_id>\w+)', views.editGroup, name="editGroup"),

    url(r'^app/add/account/user/(?P<_user_id>\w+)/(?P<_flag>\w+)$',
        views.addUserAccount,
        name="addUserAccount"
       ),
    url(r'^app/all/account/user/(?P<_user_id>\w+)$', views.viewUserAccounts, name="viewUserAccounts"),
    url(r'^app/deactivate/account/user/(?P<_user_id>\w+)/(?P<_account_id>\w+)',
        views.deactivateUserAccount,
        name="deactivateUserAccount"
       ),

    url(r'^app/add/exchanger/$', views.addExchanger, name="addExchanger"),
    url(r'^app/all/exchanger/$', views.adminExchanger, name="adminExchanger"),
    url(r'^app/edit/exchanger/(?P<_ex_id>[\w\ ]+)/(?P<_currency_id>\w+)',
        views.editExchanger,
        name="editExchanger"
       ),

    url(r'^app/add/repurchase/$', views.addRepurchaseGeneral, name="addRepurchaseGeneral"),
    url(r'^app/add/repurchase/(?P<_currency_id>\w+)$', views.addRepurchase, name="addRepurchase"),
    url(r'^app/all/repurchase/$', views.adminRepurchase, name="adminRepurchase"),
    url(r'^app/view/repurchase/(?P<_repurchase_id>\w+)$', views.viewRepurchase, name="viewRepurchase"),

    url(r'^app/admin/settings$', views.globalSettings, name="globalSettings"),

    #Dashboards
    url(r'^app/dashboard/operational/(?P<_operation_id>.+)/details$',
        views.operationDetailDashboard,
        name="operationDetailDashboard"
       ),
    url(r'^app/dashboard/operational/(?P<_operation_id>.+)/edit$',
        views.operationEditDashboard,
        name="operationEditDashboard"
       ),
    url(r'^app/dashboard/operational/(?P<_operation_id>.+)/transaction$',
        views.operationAddTransaction,
        name="operationAddTransaction"
       ),
    url(r'^app/dashboard/operational/(?P<_operation_id>.+)/history$',
        views.operationHistory,
        name="operationHistory"
       ),
    url(r'^app/transaction/(?P<_transaction_id>.+)/delete$', views.deleteTransaction, name="deleteTransaction"),

    url(r'^app/closure$', views.summaryByAlly, name="summaryByAlly"),
    url(r'^app/change/closure/(?P<_closure_id>\w+)', views.changeStatusClosure, name="changeStatusClosure"),
    url(r'^app/detail/closure/(?P<_closure_id>\w+)', views.detailClosure, name="detailClosure"),
    url(r'^app/history/closure/$', views.historyClosure, name="historyClosure"),
    
] 

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT) 
urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)

handler404 = views.handler404
handler403 = views.handler403
handler500 = views.handler500