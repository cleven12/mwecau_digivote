# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, State, Course, CollegeData

# --- Customize User Admin ---
class UserAdmin(BaseUserAdmin):
    # Define the fields to display in the list view
    list_display = ('registration_number', 'get_full_name', 'email', 'role', 'is_verified', 'course', 'state')
    list_filter = ('is_verified', 'role', 'course', 'state', 'gender', 'is_staff', 'is_superuser')
    search_fields = ('registration_number', 'first_name', 'last_name', 'email')
    ordering = ('registration_number',)
    # Define fieldsets for the edit/create form
    fieldsets = (
        (None, {'fields': ('registration_number', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'gender')}),
        (_('University Info'), {'fields': ('course', 'state', 'voter_id')}),
        (_('Permissions'), {
            'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'date_verified')}),
    )
    # Fields for creating a user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('registration_number', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('date_joined', 'last_login', 'voter_id') # Voter ID might be auto-generated

    # Optional: Add a method to display full name in list view
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

# Register the customized User admin
admin.site.register(User, UserAdmin)

# --- Customize State Admin ---
@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)
    ordering = ('name',)

# --- Customize Course Admin ---
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at', 'updated_at')
    search_fields = ('name', 'code')
    ordering = ('code',)

# --- Customize CollegeData Admin ---
@admin.register(CollegeData)
class CollegeDataAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'get_full_name', 'email', 'course', 'uploaded_by', 'is_used', 'status', 'created_at')
    list_filter = ('is_used', 'status', 'course', 'uploaded_by')
    search_fields = ('registration_number', 'first_name', 'last_name', 'email')
    ordering = ('-created_at',) # Show newest first
    # Make some fields read-only or only editable under certain conditions
    readonly_fields = ('voter_id', 'created_at') # Voter ID is auto-generated on use

    # Optional: Add a method to display full name in list view
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'

    # Optional: Add actions (e.g., mark as processed, reset status)
    actions = ['mark_as_pending', 'mark_as_processed']

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f"{updated} records were marked as pending.")
    mark_as_pending.short_description = "Mark selected records as Pending"

    def mark_as_processed(self, request, queryset):
        updated = queryset.update(status='processed')
        self.message_user(request, f"{updated} records were marked as Processed.")
    mark_as_processed.short_description = "Mark selected records as Processed"

# Optional: Customize the Admin Site header/title
admin.site.site_header = "MWECAU Election Administration"
admin.site.site_title = "MWECAU Admin Portal"
admin.site.index_title = "Welcome to the MWECAU Digital Voting System Admin Portal"

# V[01]
# from django.contrib import admin
# from .models import User, State, Course, CollegeData
# # Register your models here.

# admin.site.register(User)
# admin.site.register(State)
# admin.site.register(CollegeData)
# admin.site.register(Course)
