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
                                         'voter_id', 'gender', 'state', 'course', 'role')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Verification'), {'fields': ('is_verified', 'date_verified')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_login_ip')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name',
                       'registration_number', 'gender', 'state', 'course', 'role', 'is_verified'),
        }),
    )
    list_display = ('registration_number', 'email', 'first_name', 'last_name', 
                    'role', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'registration_number', 'voter_id')
    ordering = ('registration_number',)
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser', 'is_active', 'gender', 'state', 'course')
    readonly_fields = ('date_verified', 'last_login_ip')
    actions = ['verify_users', 'unverify_users']
    
    def verify_users(self, request, queryset):
        """Admin action to verify selected users."""
        from django.utils import timezone
        updated = queryset.filter(is_verified=False).update(is_verified=True, date_verified=timezone.now())
        self.message_user(request, f"Successfully verified {updated} user(s).")
    verify_users.short_description = "Verify selected users"
    
    def unverify_users(self, request, queryset):
        """Admin action to unverify selected users."""
        updated = queryset.filter(is_verified=True).update(is_verified=False, date_verified=None)
        self.message_user(request, f"Successfully unverified {updated} user(s).")
    unverify_users.short_description = "Unverify selected users"

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