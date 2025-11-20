# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, State, Course, CollegeData

class UserAdmin(BaseUserAdmin):
    list_display = ('registration_number', 'get_full_name', 'email', 'role', 'is_verified', 'course', 'state')
    list_filter = ('is_verified', 'role', 'course', 'state', 'gender', 'is_staff', 'is_superuser')
    search_fields = ('registration_number', 'first_name', 'last_name', 'email')
    ordering = ('registration_number',)

    fieldsets = (
        (None, {'fields': ('registration_number', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'gender')}),
        (_('University Info'), {'fields': ('course', 'state', 'voter_id')}),
        (_('Permissions'), {
            'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'date_verified')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('registration_number', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('date_joined', 'last_login', 'voter_id')

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at', 'updated_at')
    search_fields = ('name', 'code')
    ordering = ('code',)

@admin.register(CollegeData)
class CollegeDataAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'get_full_name', 'email', 'course', 'uploaded_by', 'is_used', 'status', 'created_at')
    list_filter = ('is_used', 'status', 'course', 'uploaded_by')
    search_fields = ('registration_number', 'first_name', 'last_name', 'email')
    ordering = ('-created_at',)
    readonly_fields = ('voter_id', 'created_at')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    
    get_full_name.short_description = 'Full Name'
    actions = ['mark_as_pending', 'mark_as_processed']

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f"{updated} records were marked as pending.")
    mark_as_pending.short_description = "Mark selected records as Pending"

    def mark_as_processed(self, request, queryset):
        updated = queryset.update(status='processed')
        self.message_user(request, f"{updated} records were marked as Processed.")

    mark_as_processed.short_description = "Mark selected records as Processed"



admin.site.register(User, UserAdmin)

admin.site.site_header = "MWECAU Election Administration"
admin.site.site_title = "MWECAU Admin Portal"
admin.site.index_title = "Welcome to the MWECAU Digital Voting System Admin Portal"