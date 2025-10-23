from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class RegistrationNumberBackend(ModelBackend):
    """Authentication backend that uses registration_number instead of username."""
    
    def authenticate(self, request, registration_number=None, password=None, **kwargs):
        """Authenticate using registration_number and password."""
        if registration_number is None or password is None:
            return None
        
        try:
            user = User.objects.get(registration_number=registration_number)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            User().set_password(password)
        return None
    
    def get_user(self, user_id):
        """Get user by primary key."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
