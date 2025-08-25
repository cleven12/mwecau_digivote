from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import User

# Celery tasks for email notifications
@shared_task(queue='email_queue')
def send_verification_email(user_id, voter_token=None):
    """Send verification email with user details and optional VoterToken."""
    user = User.objects.get(id=user_id)
    subject = "MWECAU Election Platform - Account Verification"
    message = (
        f"Dear {user.get_full_name()},\n\n"
        f"Your account has been verified:\n"
        f"- Registration Number: {user.registration_number}\n"
        f"- Email: {user.email}\n"
        f"- Course: {user.course.name if user.course else 'N/A'}\n"
        f"- State: {user.state.name if user.state else 'N/A'}\n"
        f"- Voter ID: {user.voter_id}\n"
    )
    if voter_token:
        message += f"- Voter Token for {voter_token.election.title}: {voter_token.token}\n"
    message += "Log in at http://localhost:8000/api/auth/login/ to participate in elections."
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=True,
    )

@shared_task(queue='email_queue')
def send_password_reset_email(user_id, new_password):
    """Send password reset email with new password."""
    user = User.objects.get(id=user_id)
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
        fail_silently=True,
    )

@shared_task(queue='email_queue')
def send_commissioner_contact_email(user_id, message_content):
    """Send contact message to commissioners."""
    user = User.objects.get(id=user_id)
    commissioners = User.objects.filter(role=User.ROLE_COMMISSIONER, is_verified=True)
    subject = "MWECAU Election Platform - User Contact Request"
    message = (
        f"Message from {user.get_full_name()} ({user.registration_number}):\n\n"
        f"{message_content}\n\n"
        f"Reply to: {user.email}"
    )
    recipient_list = [comm.email for comm in commissioners if comm.email]
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=recipient_list,
        fail_silently=True,
    )