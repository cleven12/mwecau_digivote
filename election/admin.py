from django.contrib import admin
from .models import ElectionLevel, Election, Position, Candidate, Vote

@admin.register(ElectionLevel)
class ElectionLevelAdmin(admin.ModelAdmin):
    """Admin configuration for ElectionLevel model."""
    list_display = ('name', 'code', 'description')
    search_fields = ('name', 'code')

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    """Admin configuration for Election model."""
    list_display = ('title', 'start_date', 'end_date', 'is_active', 'has_ended')
    search_fields = ('title', 'description')
    list_filter = ('is_active', 'has_ended')
    date_hierarchy = 'start_date'

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin configuration for Position model."""
    list_display = ('title', 'election_level', 'gender_restriction')
    search_fields = ('title',)
    list_filter = ('election_level', 'gender_restriction')

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Admin configuration for Candidate model."""
    list_display = ('user', 'election', 'position')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 
                     'election__title', 'position__title')
    list_filter = ('election', 'position')

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin configuration for Vote model."""
    list_display = ('voter', 'candidate', 'timestamp')
    search_fields = ('voter__first_name', 'voter__last_name', 'voter__email',
                    'candidate__user__first_name', 'candidate__user__last_name')
    list_filter = ('candidate__election', 'candidate__position', 'timestamp')
    date_hierarchy = 'timestamp'