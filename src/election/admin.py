# election/admin.py

from django.contrib import admin
from django.utils import timezone
from .models import Election, ElectionLevel, Position, Candidate, VoterToken, Vote


@admin.register(ElectionLevel)
class ElectionLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'type', 'course', 'state')
    list_filter = ('type', 'course', 'state')
    search_fields = ('name', 'code', 'description')
    ordering = ('type', 'name')
    autocomplete_fields = ['course', 'state']
    
    # Ensure model's clean() method is called
    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'is_active', 'has_ended', 'created_at')
    list_filter = ('is_active', 'has_ended', 'start_date', 'end_date', 'levels')
    search_fields = ('title', 'description')
    ordering = ('-start_date',)
    filter_horizontal = ('levels',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['activate_elections', 'deactivate_elections', 'mark_as_ended', 'mark_as_not_ended']

    def activate_elections(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} election(s) were successfully activated.")
    activate_elections.short_description = "Activate selected elections"

    def deactivate_elections(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} election(s) were successfully deactivated.")
    deactivate_elections.short_description = "Deactivate selected elections"

    def mark_as_ended(self, request, queryset):
        updated = queryset.update(has_ended=True, is_active=False)
        self.message_user(request, f"{updated} election(s) were successfully marked as ended.")
    mark_as_ended.short_description = "Mark selected elections as ended"

    def mark_as_not_ended(self, request, queryset):
        updated = queryset.update(has_ended=False)
        self.message_user(request, f"{updated} election(s) were successfully marked as not ended.")
    mark_as_not_ended.short_description = "Mark selected elections as NOT ended"


class PositionInline(admin.TabularInline):
    model = Position
    extra = 1


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'election_level', 'gender_restriction')
    list_filter = ('election_level__type', 'election_level', 'gender_restriction')
    search_fields = ('title', 'description', 'election_level__name')
    ordering = ('election_level', 'title')
    
    # Use autocomplete for ElectionLevel
    autocomplete_fields = ['election_level']


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'election', 'position', 'created_at')
    list_filter = (
        'election', 
        'position__election_level__type', 
        'position__election_level',
        'position', 
        'created_at'
    )
    search_fields = (
        'user__first_name', 
        'user__last_name', 
        'user__registration_number', 
        'election__title', 
        'position__title',
        'bio'
    )
    ordering = ('-created_at',)
    
    autocomplete_fields = ['user', 'election', 'position']
    readonly_fields = ('created_at', 'updated_at')

@admin.register(VoterToken)
class VoterTokenAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'election', 'election_level', 'is_used', 'expiry_date', 'created_at')
    list_filter = ('is_used', 'election', 'election_level__type', 'election_level', 'created_at', 'expiry_date')
    search_fields = (
        'user__first_name', 
        'user__last_name', 
        'user__registration_number', 
        'election__title',
        'token'
    )
    ordering = ('-created_at',)
    readonly_fields = ('token', 'created_at', 'used_at') 
    autocomplete_fields = ['user', 'election', 'election_level']
    actions = ['invalidate_tokens']

    def invalidate_tokens(self, request, queryset):
        # Mark tokens as used without setting used_at (or set it to now)
        updated_count = queryset.update(is_used=True) 
        self.message_user(request, f"{updated_count} token(s) were marked as used.")
    invalidate_tokens.short_description = "Invalidate selected tokens (Mark as used)"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'timestamp')
    list_filter = (
        'election', 
        'election_level__type', 
        'election_level', 
        'candidate__position', 
        'timestamp'
    )
    search_fields = (
        'token__user__first_name',
        'token__user__last_name',
        'token__user__registration_number',
        'candidate__user__first_name',
        'candidate__user__last_name',
        'election__title'
    )
    ordering = ('-timestamp',)
    readonly_fields = [f.name for f in Vote._meta.get_fields()] 