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
    
    # Use autocomplete for Course/State if there are many entries
    autocomplete_fields = ['course', 'state']
    
    # Ensure the model's clean() method is called
    def save_model(self, request, obj, form, change):
        obj.full_clean() # This calls the model's clean() method
        super().save_model(request, obj, form, change)

    # Optional: Add a description/help text to the admin change form
    # This requires defining a ModelAdmin class attribute or using a custom template
    # For simplicity, relying on model field help_text for now.

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'is_active', 'has_ended', 'created_at')
    list_filter = ('is_active', 'has_ended', 'start_date', 'end_date', 'levels')
    search_fields = ('title', 'description')
    ordering = ('-start_date',)
    filter_horizontal = ('levels',) # Better UI for M2M selection
    readonly_fields = ('created_at', 'updated_at')
    
    # Actions to quickly change election status
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
        updated = queryset.update(has_ended=True, is_active=False) # Often, ended elections are also inactive
        self.message_user(request, f"{updated} election(s) were successfully marked as ended.")
    mark_as_ended.short_description = "Mark selected elections as ended"

    def mark_as_not_ended(self, request, queryset):
        updated = queryset.update(has_ended=False)
        self.message_user(request, f"{updated} election(s) were successfully marked as not ended.")
    mark_as_not_ended.short_description = "Mark selected elections as NOT ended"


class PositionInline(admin.TabularInline): # Or StackedInline
    model = Position
    extra = 1 # Number of empty forms to display
    # Consider adding autocomplete for related models if needed within inline


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'election_level', 'gender_restriction')
    list_filter = ('election_level__type', 'election_level', 'gender_restriction') # Filter by level type and specific level
    search_fields = ('title', 'description', 'election_level__name')
    ordering = ('election_level', 'title')
    
    # Use autocomplete for ElectionLevel
    autocomplete_fields = ['election_level']


class CandidateInline(admin.TabularInline): # Or StackedInline
    model = Candidate
    extra = 1
    # Consider readonly fields for election if it's set by the parent view
    # readonly_fields = ('election',) # If election is passed from Election admin


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'election', 'position', 'created_at')
    list_filter = (
        'election', 
        'position__election_level__type', # Filter by election level type (President, Course, State)
        'position__election_level',       # Filter by specific election level
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
    
    # Use autocomplete for related models
    autocomplete_fields = ['user', 'election', 'position']
    readonly_fields = ('created_at', 'updated_at')

    # Optional: Improve image display in list view (requires Pillow)
    # def candidate_image(self, obj):
    #     if obj.image:
    #         return format_html('<img src="{}" style="width: 50px; height:50px;" />', obj.image.url)
    #     return "No Image Found"
    # candidate_image.short_description = 'Image'


@admin.register(VoterToken)
class VoterTokenAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'election', 'election_level', 'is_used', 'expiry_date', 'created_at')
    list_filter = ('is_used', 'election', 'election_level__type', 'election_level', 'created_at', 'expiry_date')
    search_fields = (
        'user__first_name', 
        'user__last_name', 
        'user__registration_number', 
        'election__title',
        'token' # Search by UUID string
    )
    ordering = ('-created_at',)
    readonly_fields = ('token', 'created_at', 'used_at') # Token and timestamps are system-managed
    
    # Use autocomplete for related models
    autocomplete_fields = ['user', 'election', 'election_level']

    # Optional: Add a custom action to invalidate tokens (mark as used/expired)
    actions = ['invalidate_tokens']

    def invalidate_tokens(self, request, queryset):
        # Mark tokens as used without setting used_at (or set it to now)
        updated_count = queryset.update(is_used=True) 
        # Note: This doesn't call mark_as_used, so used_at won't be set.
        # If used_at is important, loop and call mark_as_used on each.
        # Or create a more complex action.
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
    # Make all fields readonly as votes should generally not be edited manually
    readonly_fields = [f.name for f in Vote._meta.get_fields()] 

    # Optional: Add a custom action to export votes (requires extra setup)
    # actions = ['export_votes']

    # If you want to display related info more easily in the list view:
    # def voter_name(self, obj):
    #     return obj.token.user.get_full_name()
    # voter_name.short_description = 'Voter'

    # def candidate_name(self, obj):
    #     return obj.candidate.user.get_full_name()
    # candidate_name.short_description = 'Candidate Voted For'
