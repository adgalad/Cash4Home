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
    url(r'^v1/admin/', admin.site.urls),
    url(r'^v1/signup/$', views.signup, name='signup'),
    url(r'^v1/login/', views.login, name='login'),
    url(r'^v1/logout/$', views.logout, name='logout'),


    # Reset Password
    url(r'^v1/password_reset/$', views.password_reset, name='password_reset'),
    url(r'^v1/password_reset/done/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^v1/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        name='password_reset_confirm'
       ),
    url(r'^v1/reset/done/$', auth_views.password_reset_complete, name='password_reset_complete'),

    #User
    url(r'^v1/dashboard$', views.dashboard, name='dashboard'),
    url(r'^v1/dashboard/closure$', views.closureTransactionModal, name='closureTransactionModal'),
    url(r'^v1/user/profile$', views.profile, name='profile'),
    url(r'^v1/user/verification$', views.userVerification, name='userVerification'),

    url(r'^v1/emailVerification$', views.resendEmailVerification, name="resendEmailVerification"),
    url(r'^v1/activateEmail/(?P<token>.+)$', views.activateEmail, name="activateEmail"),

    url(r'^v1/accounts$', views.accounts, name='accounts'),
    url(r'^v1/account/new$', views.createAccount, name='createAccount'),
    url(r'^v1/account/edit/(?P<pk>.+)$', views.editAccountDetails, name='editAccountDetails'),

    url(r'^v1/operation/new$', views.createOperation, name='createOperation'),
    url(r'^v1/operation/verify/(?P<_operation_id>.+)$', views.verifyOperation, name='verifyOperation'),
    url(r'^v1/operation/pending$', views.pendingOperations, name='pendingOperations'),
    url(r'^v1/operation/(?P<_operation_id>.+)/details$', views.operationModal, name='operationModal'),
    url(r'^v1/operation/(?P<_operation_id>.+)/cancel$', views.cancelOperation, name='cancelOperation'),
    url(r'^v1/operation/(?P<_operation_id>.+)/claim$', views.claimOperation, name='claimOperation'),

    url(r'^v1/help$', views.home, name='help'),
    url(r'^v1/$', views.home, name='home'),
    url(r'^v1/index$', views.home, name='home'),
    url(r'^v1/index\.html$', views.home, name='home'),
    url(r'^v1/company$', views.company, name="company"), # Solo por prueba

    url(r'^v1/accounts/profile/$', views.home, name="home"), # Solo por prueba

    #Admin
    url(r'^v1/add/currency/$', views.addCurrencies, name="addCurrencies"),
    url(r'^v1/all/currency/$', views.adminCurrencies, name="adminCurrencies"),
    url(r'^v1/edit/currency/(?P<_currency_id>\w+)', views.editCurrencies, name="editCurrencies"),

    url(r'^v1/add/exchange_rate/$', views.addExchangeRate, name="addExchangeRate"),
    url(r'^v1/all/exchange_rate/$', views.adminExchangeRate, name="adminExchangeRate"),
    url(r'^v1/edit/exchange_rate/(?P<_rate_id>\w+)', views.editExchangeRate, name="editExchangeRate"),
    url(r'^v1/all/exchange_rate/(?P<_rate_id>\w+)', views.historyExchangeRate, name="historyExchangeRate"),

    url(r'^v1/add/bank/$', views.addBank, name="addBank"),
    url(r'^v1/all/bank/$', views.adminBank, name="adminBank"),
    url(r'^v1/edit/bank/(?P<_bank_id>\w+)', views.editBank, name="editBank"),

    url(r'^v1/add/account/$', views.addAccount, name="addAccount"),
    url(r'^v1/all/account/$', views.adminAccount, name="adminAccount"),
    url(r'^v1/edit/account/(?P<_account_id>\w+)', views.editAccount, name="editAccount"),

    url(r'^v1/add/user/$', views.addUser, name="addUser"),
    url(r'^v1/all/user/$', views.adminUser, name="adminUser"),
    url(r'^v1/edit/user/(?P<_user_id>\w+)', views.editUser, name="editUser"),
    url(r'^v1/view/user/(?P<_user_id>\w+)', views.viewUser, name="viewUser"),
    url(r'^v1/verify/user/(?P<_user_id>\w+)', views.verifyUser, name="verifyUser"),

    url(r'^v1/add/holiday/$', views.addHoliday, name="addHoliday"),
    url(r'^v1/all/holiday/$', views.adminHoliday, name="adminHoliday"),
    url(r'^v1/edit/holiday/(?P<_holiday_id>\w+)', views.editHoliday, name="editHoliday"),

    url(r'^v1/add/country/$', views.addCountry, name="addCountry"),
    url(r'^v1/all/country/$', views.adminCountry, name="adminCountry"),
    url(r'^v1/edit/country/(?P<_country_id>[\w\ ]+)', views.editCountry, name="editCountry"),

    url(r'^v1/add/group$', views.addGroup, name="addGroup"),
    url(r'^v1/all/group/$', views.adminGroup, name="adminGroup"),
    url(r'^v1/edit/group/(?P<_group_id>\w+)', views.editGroup, name="editGroup"),

    url(r'^v1/add/account/user/(?P<_user_id>\w+)/(?P<_flag>\w+)$',
        views.addUserAccount,
        name="addUserAccount"
       ),
    url(r'^v1/all/account/user/(?P<_user_id>\w+)$', views.viewUserAccounts, name="viewUserAccounts"),
    url(r'^v1/deactivate/account/user/(?P<_user_id>\w+)/(?P<_account_id>\w+)',
        views.deactivateUserAccount,
        name="deactivateUserAccount"
       ),

    url(r'^v1/add/exchanger/$', views.addExchanger, name="addExchanger"),
    url(r'^v1/all/exchanger/$', views.adminExchanger, name="adminExchanger"),
    url(r'^v1/edit/exchanger/(?P<_ex_id>[\w\ ]+)/(?P<_currency_id>\w+)',
        views.editExchanger,
        name="editExchanger"
       ),

    url(r'^v1/add/repurchase/$', views.addRepurchaseGeneral, name="addRepurchaseGeneral"),
    url(r'^v1/add/repurchase/(?P<_currency_id>\w+)$', views.addRepurchase, name="addRepurchase"),
    url(r'^v1/all/repurchase/$', views.adminRepurchase, name="adminRepurchase"),
    url(r'^v1/view/repurchase/(?P<_repurchase_id>\w+)$', views.viewRepurchase, name="viewRepurchase"),

    url(r'^v1/admin/settings$', views.globalSettings, name="globalSettings"),

    #Dashboards
    url(r'^v1/dashboard/operational/(?P<_operation_id>.+)/details$',
        views.operationDetailDashboard,
        name="operationDetailDashboard"
       ),
    url(r'^v1/dashboard/operational/(?P<_operation_id>.+)/edit$',
        views.operationEditDashboard,
        name="operationEditDashboard"
       ),
    url(r'^v1/dashboard/operational/(?P<_operation_id>.+)/transaction$',
        views.operationAddTransaction,
        name="operationAddTransaction"
       ),
    url(r'^v1/dashboard/operational/(?P<_operation_id>.+)/history$',
        views.operationHistory,
        name="operationHistory"
       ),
    url(r'^v1/transaction/(?P<_transaction_id>.+)/delete$', views.deleteTransaction, name="deleteTransaction"),

    url(r'^v1/closure$', views.summaryByAlly, name="summaryByAlly"),
    url(r'^v1/change/closure/(?P<_closure_id>\w+)', views.changeStatusClosure, name="changeStatusClosure"),
    url(r'^v1/detail/closure/(?P<_closure_id>\w+)', views.detailClosure, name="detailClosure"),
    url(r'^v1/history/closure/$', views.historyClosure, name="historyClosure"),
    
] 

urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT) 
urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)

handler404 = views.handler404
handler403 = views.handler403
handler500 = views.handler500