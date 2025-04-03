from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, Role, UserLoginLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'mobile', 'name', 'department', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'department')
    search_fields = ('username', 'email', 'mobile', 'name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('name', 'email', 'mobile', 'avatar')}),
        (_('Organizational info'), {'fields': ('department', 'position')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'real_name', 'gender', 'birthday')
    list_filter = ('gender',)
    search_fields = ('user__username', 'real_name')
    raw_id_fields = ('user',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'role_code', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('role_name', 'role_code', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserLoginLog)
class UserLoginLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_type', 'login_time', 'status')
    list_filter = ('login_type', 'status', 'login_time')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('login_time',)
    ordering = ('-login_time',) 