from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.

admin.site.register(Role)
admin.site.register(Department)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Additional info', {'fields': ('role', 'department')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'department'),
        }),
    )

    # Pole tylko do odczytu
    readonly_fields = ('created_at',)

    list_display = ('username', 'email', 'role', 'department', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'role__role_name', 'department__department_name')
    ordering = ('username',)