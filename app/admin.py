from django import forms
from django.contrib import admin
from django.contrib.auth import password_validation
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.utils.translation import gettext, gettext_lazy as _
from .models import User
from app.models import *

class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput,
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )


    class Meta:
        model = User
        fields = ('email', 'is_staff', 'is_active', 'first_name', 'last_name', )

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class UserChangeForm(BaseUserChangeForm):
    """
    Override as needed
    """

class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'is_superuser', 'is_staff', 'is_active', 'first_name', 'last_name', 'created_at', 'updated_at', 'last_login')
    # list_filter = ('email',)

    readonly_fields=('created_at', 'updated_at',)
    fieldsets = (
        (None                , {'fields': ('email', 'password')}),
        (_('Personal info')  , {'fields': ('first_name', 'last_name',)}),
        (_('Permissions')    , {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    # filter_horizontal = ()

class HolidayAdmin(admin.ModelAdmin):
    pass

class CurrencyAdmin(admin.ModelAdmin):
    pass

class ExchangeRateAdmin(admin.ModelAdmin):
    pass

class BankAdmin(admin.ModelAdmin):
    pass

class AccountAdmin(admin.ModelAdmin):
    pass

class AccountBelongsToAdmin(admin.ModelAdmin):
    pass

class OperationAdmin(admin.ModelAdmin):
    pass

class OperationGoesToAdmin(admin.ModelAdmin):
    pass

class TransactionAdmin(admin.ModelAdmin):
    pass

class RepurchaseAdmin(admin.ModelAdmin):
    pass

class RepurchaseCameFromAdmin(admin.ModelAdmin):
    pass

class ComissionAdmin(admin.ModelAdmin):
    pass

class CountryAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Holiday, HolidayAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(ExchangeRate, ExchangeRateAdmin)
admin.site.register(Bank, BankAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(AccountBelongsTo, AccountBelongsToAdmin)
admin.site.register(Operation, OperationAdmin)
admin.site.register(OperationGoesTo, OperationGoesToAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Repurchase, RepurchaseAdmin)
admin.site.register(RepurchaseCameFrom, RepurchaseCameFromAdmin)
admin.site.register(Comission, ComissionAdmin)
admin.site.register(Country, CountryAdmin)