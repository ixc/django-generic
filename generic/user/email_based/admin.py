from django.contrib.auth import admin
from django.utils.translation import ugettext_lazy as _
from . import forms, models

class UserAdmin(admin.UserAdmin):
    form = forms.UserChangeForm
    add_form = forms.UserCreationForm

    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password',)}),
        (_('Personal info'), {'fields': ('first_name', 'last_name',)}),
        (_('Permissions'), {'fields': (
            'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None, {
                'classes': ('wide',),
                'fields': (
                    'email', 'first_name', 'last_name',
                    'password1', 'password2',
                )
            }
        ),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('last_name', 'first_name', 'email',)

