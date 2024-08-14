from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    search_fields = ['username', 'email']


CustomUserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar', 'role')}),
)

admin.site.register(User, CustomUserAdmin)
