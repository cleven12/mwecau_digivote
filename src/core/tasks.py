from asyncio.log import logger
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from election.models import Election, ElectionLevel, VoterToken 
import uuid


@shared_task(queue='email_queue')
def send_verification_email(user_id):
    """
    Send verification email to user when they are verified.
    Generates tokens for all active elections they're eligible for.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found for verification email.")
        return

    if not user.email:
        logger.warning(f"User {user_id} has no email, skipping verification email")
        return
    
    if not user.is_verified:
        print(f"User {user_id} is not verified, skipping token generation")
        return

    # Get all active elections
    active_elections = Election.objects.filter(is_active=True, has_ended=False)

    if not active_elections.exists():
        # No active elections, send simple verification email
        subject = "MWECAU DigiVote - Registration Confirmed"
        message = (
            f"Dear {user.get_full_name()},\n\n"
            f"Welcome to the MWECAU DigiVote!\n\n"
            f"Your account has been verified. You are now registered as a voter.\n"
            f"Your Voter ID: {user.voter_id}\n\n"
            f"You will receive notification emails when new elections are activated.\n\n"
            f"Regards,\nMWECAU Election Commission"
        )
    else:
        # Generate tokens for active elections and include in email
        tokens_by_election = {}
        for election in active_elections:
            tokens = []
            for level in election.levels.select_related('course', 'state').all():
                eligible = _check_eligibility(user, level)
                if eligible:
                    expiry = election.end_date
                    token, created = VoterToken.objects.get_or_create(
                        user=user,
                        election=election,
                        election_level=level,
                        defaults={
                            'token': uuid.uuid4(),
                            'expiry_date': expiry
                        }
                    )
                    if not token.is_used:
                        tokens.append((level.name, str(token.token)))
            
            if tokens:
                tokens_by_election[election.title] = tokens
        
        if tokens_by_election:
            tokens_text = ""
            for election_title, tokens in tokens_by_election.items():
                tokens_text += f"\n{election_title}:\n"
                for level_name, token in tokens:
                    tokens_text += f"  - {level_name}: {token}\n"
            
            subject = "MWECAU DigiVote - Registration Confirmed"
            message = (
                f"Dear {user.get_full_name()},\n\n"
                f"Welcome to the MWECAU DigiVote!\n\n"
                f"Your account has been verified. You are now registered as a voter.\n"
                f"Your Voter ID: {user.voter_id}\n\n"
                f"You have been assigned to the following active elections:\n"
                f"{tokens_text}\n"
                f"Keep your voter tokens secure and do not share them.\n"
                f"Vote at the election platform during the voting period.\n\n"
                f"Regards,\nMWECAU Election Commission"
            )
        else:
            subject = "MWECAU DigiVote - Registration Confirmed"
            message = (
                f"Dear {user.get_full_name()},\n\n"
                f"Welcome to the MWECAU DigiVote!\n\n"
                f"Your account has been verified. You are now registered as a voter.\n"
                f"Your Voter ID: {user.voter_id}\n\n"
                f"You will receive notification emails when you become eligible for elections.\n\n"
                f"Regards,\nMWECAU Election Commission"
            )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'mwecauictclub@gmail.com',
            recipient_list=[user.email],
            fail_silently=False
        )
        print(f"Verification email sent to {user.email}")
    except Exception as e:
        print(f"Error sending verification email: {e}")



@shared_task(queue='email_queue')
def send_password_reset_email(user_id, uid, token):
    """Send password reset email with a secure time-limited link."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        print(f"User with ID {user_id} not found for password reset email.")
        return

    if not user.email:
        return

    reset_url = f"{settings.SITE_URL}/password-reset/confirm/{uid}/{token}/"
    subject = "MWECAU DigiVote - Password Reset Request"
    message = (
        f"Dear {user.get_full_name()},\n\n"
        f"A password reset was requested for your MWECAU DigiVote account "
        f"({user.registration_number}).\n\n"
        f"Click the link below to set a new password (expires in 1 hour):\n"
        f"{reset_url}\n\n"
        f"If you did not request a password reset, ignore this email — your "
        f"account is safe and your password has not changed.\n\n"
        f"Regards,\nMWECAU Election Commission"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'mwecauictclub@gmail.com',
        recipient_list=[user.email],
        fail_silently=True,
    )


@shared_task(queue='email_queue')
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
        return

    subject = "MWECAU DigiVote - User Contact Request"
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
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'mwecauictclub@gmail.com',
            recipient_list=recipient_list,
            fail_silently=True,
        )
    else:
        print("No valid email addresses found for commissioners.")


def _check_eligibility(user, level):
    """
    Helper function to check if a user is eligible for an election level.
    """
    if level.type == ElectionLevel.TYPE_PRESIDENT:
        return True
    elif level.type == ElectionLevel.TYPE_COURSE:
        return user.course is not None and level.course_id == user.course_id
    elif level.type == ElectionLevel.TYPE_STATE:
        return user.state is not None and level.state_id == user.state_id
    return False

