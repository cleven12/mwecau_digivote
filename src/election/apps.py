from django.apps import AppConfig

class ElectionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'election'
    
    def ready(self):
        """Import and register signals when the app is ready."""
        import election.signals  # Register signals