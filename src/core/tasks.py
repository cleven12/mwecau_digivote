# core/tasks.py
from django.core.mail import send_mail
from django.conf import settings
from .models import User
# Import election models here as they are needed for token generation
from election.models import Election, VoterToken 
import uuid

# email notifications
def send_verification_email(user_id):
    """Send verification/welcome email. 
       Includes VoterTokens only if active elections exist.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # Log error or handle appropriately
        print(f"User with ID {user_id} not found for email.")
        return

    # Check for active elections
    active_elections = Election.objects.filter(is_active=True, has_ended=False)
    has_active_elections = active_elections.exists()

    subject = "MWECAU Election Platform - Account Verified"
    message = (
        f"Dear {user.get_full_name()},\n\n"
        f"Your account has been successfully verified!\n"
        f"- Registration Number: {user.registration_number}\n"
        f"- Email: {user.email}\n"
        f"- Course: {user.course.name if user.course else 'N/A'}\n"
        f"- State: {user.state.name if user.state else 'N/A'}\n"
        f"- Voter ID: {user.voter_id}\n"
    )
    
    if has_active_elections:
        message += "\nYou are eligible to vote in the following active elections:\n"
        voter_tokens = []
        for election in active_elections:
            # Get or create the token for this user-election pair
            token_obj, created = VoterToken.objects.get_or_create(
                user=user,
                election=election,
                defaults={'token': uuid.uuid4()}
            )
            voter_tokens.append(f"  - {election.title}: {token_obj.token}")
        
        message += "\n".join(voter_tokens)
        message += "\n\nUse these tokens to cast your votes."

    message += "\n\nLog in at http://localhost:8000/api/auth/login/ to participate."

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False, # Better for debugging, consider True in production
    )


def send_password_reset_email(user_id, new_password):
    """Send password reset email with new password."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        print(f"User with ID {user_id} not found for password reset email.")
        return
        
    subject = "MWECAU Election Platform - Password Reset"
    message = (
        f"Dear {user.get_full_name()},\n\n"
        f"Your password has been reset:\n"
        f"- Registration Number: {user.registration_number}\n"
        f"- New Password: {new_password}\n"
        f"Log in at http://localhost:8000/api/auth/login/ with your new password."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=False,
    )

def send_commissioner_contact_email(user_id, message_content):
    """Send contact message to commissioners."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        print(f"User with ID {user_id} not found for contact email.")
        return

    commissioners = User.objects.filter(role=User.ROLE_COMMISSIONER, is_verified=True)
    if not commissioners.exists():
        print("No verified commissioners found to send contact message.")
        return # Or handle differently

    subject = "MWECAU Election Platform - User Contact Request"
    message = (
        f"Message from {user.get_full_name()} ({user.registration_number}):\n\n"
        f"{message_content}\n\n"
        f"Reply to: {user.email}"
    )
    recipient_list = [comm.email for comm in commissioners if comm.email]
    
    if recipient_list:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipient_list,
            fail_silently=False,
        )
    else:
        print("No valid email addresses found for commissioners.")