from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages
from .models import ElectionLevel, Election, Position, Candidate, Vote, VoterToken


@admin.register(ElectionLevel)
class ElectionLevelAdmin(admin.ModelAdmin):
    """Admin configuration for ElectionLevel model."""
    list_display = ('name', 'code', 'type', 'related_scope', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('type', 'course', 'state')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('type', 'name')

    def related_scope(self, obj):
        """Display related course/state depending on the level type."""
        if obj.type == obj.TYPE_COURSE and obj.course:
            return obj.course.name
        elif obj.type == obj.TYPE_STATE and obj.state:
            return obj.state.name
        return "-"
    related_scope.short_description = "Course/State"


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    """Admin configuration for Election model."""
    list_display = (
        'title',
        'start_date_local',
        'end_date_local',
        'is_active',
        'has_ended',
        'status_display',
    )
    search_fields = ('title', 'description')
    list_filter = ('is_active', 'has_ended', 'levels')
    filter_horizontal = ('levels',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-start_date',)
    date_hierarchy = None  # 🔹 Disabled to avoid timezone DB errors
    actions = ['activate_and_notify']

    def start_date_local(self, obj):
        return timezone.localtime(obj.start_date).strftime("%Y-%m-%d %H:%M")
    start_date_local.short_description = "Start Date"

    def end_date_local(self, obj):
        return timezone.localtime(obj.end_date).strftime("%Y-%m-%d %H:%M")
    end_date_local.short_description = "End Date"

    def status_display(self, obj):
        now = timezone.now()
        if obj.has_ended:
            color, label = "gray", "Ended"
        elif obj.is_active:
            color, label = "green", "Active"
        elif obj.start_date > now:
            color, label = "blue", "Upcoming"
        else:
            color, label = "orange", "Inactive"
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', color, label)
    status_display.short_description = "Status"

    def activate_and_notify(self, request, queryset):
        """Admin action to activate selected elections and generate/send voter tokens."""
        updated = 0
        for obj in queryset:
            try:
                # Use model method which also triggers notify_voters_of_active_election
                obj.activate()
                updated += 1
            except Exception as e:
                self.message_user(request, f"Failed to activate election {obj.id}: {e}", level=messages.ERROR)

        if updated:
            self.message_user(request, f"Activated and notified {updated} election(s).", level=messages.SUCCESS)
    activate_and_notify.short_description = "Activate selected elections and notify voters"


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin configuration for Position model."""
    list_display = ('title', 'election_level', 'gender_restriction')
    search_fields = ('title',)
    list_filter = ('election_level', 'gender_restriction')
    readonly_fields = ()
    ordering = ('election_level', 'title')


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Admin configuration for Candidate model."""
    list_display = ('user', 'election', 'position', 'vote_count', 'created_at')
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email',
        'election__title', 'position__title'
    )
    list_filter = ('election', 'position__election_level')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('election', 'position')
    autocomplete_fields = ('user', 'election', 'position')

    def candidate_image(self, obj):
        """Display image preview if available."""
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" style="border-radius:50%;" />', obj.image.url)
        return "No image"
    candidate_image.short_description = "Profile Picture"


@admin.register(VoterToken)
class VoterTokenAdmin(admin.ModelAdmin):
    """Admin configuration for VoterToken model."""
    list_display = ('user', 'election', 'election_level', 'token', 'is_used', 'expiry_date_local')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'token')
    list_filter = ('is_used', 'election', 'election_level')
    readonly_fields = ('created_at', 'used_at')
    ordering = ('-created_at',)

    def expiry_date_local(self, obj):
        return timezone.localtime(obj.expiry_date).strftime("%Y-%m-%d %H:%M")
    expiry_date_local.short_description = "Expiry Date"


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin configuration for Vote model."""
    list_display = ('voter', 'candidate', 'election', 'election_level', 'timestamp_local')
    search_fields = (
        'voter__first_name', 'voter__last_name', 'voter__email',
        'candidate__user__first_name', 'candidate__user__last_name',
        'election__title'
    )
    list_filter = ('election', 'election_level', 'timestamp')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    date_hierarchy = None  # 🔹 Disable to prevent timezone issues

    def timestamp_local(self, obj):
        return timezone.localtime(obj.timestamp).strftime("%Y-%m-%d %H:%M")
    timestamp_local.short_description = "Time (Local)"
