from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, State, Course, CollegeData

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model."""
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'registration_number', 
                                         'voter_id', 'state', 'course', 'role')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name',
                       'registration_number', 'state', 'course', 'role'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'registration_number', 
                    'voter_id', 'role', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'registration_number', 'voter_id')
    ordering = ('email',)
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    """Admin configuration for State model."""
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin configuration for Course model."""
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(CollegeData)
class CollegeDataAdmin(admin.ModelAdmin):
    """Admin configuration for CollegeData model."""
    list_display = ('registration_number', 'first_name', 'last_name', 'course', 'is_used')
    search_fields = ('registration_number', 'first_name', 'last_name')
    list_filter = ('course', 'is_used')