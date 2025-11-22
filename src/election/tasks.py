from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from core.models import User
from .models import Election, ElectionLevel, Position, VoterToken
import uuid


@shared_task(queue='email_queue')
def notify_voters_of_active_election(election_id):
    """Send email notifications with per-level VoterTokens when an election is activated."""
    election = Election.objects.get(id=election_id)
    if not election.is_ongoing():
        return

    voters = User.objects.filter(is_verified=True, voter_id__isnull=False)

    print(f"notify_voters_of_active_election: election={election.id} voters_count={voters.count()}")

    for user in voters:
        tokens = []
        debug_reasons = []
        for level in election.levels.select_related('course', 'state').all():
            eligible = False
            reason = None

            if level.type == ElectionLevel.TYPE_PRESIDENT:
                eligible = True
                reason = 'president-level'

            elif level.type == ElectionLevel.TYPE_COURSE:
                if user.course is None:
                    eligible = False
                    reason = 'user-no-course'
                elif level.course_id == user.course_id:
                    eligible = True
                    reason = f'course-match ({user.course_id})'
                else:
                    eligible = False
                    reason = f'course-mismatch (level={level.course_id} user={user.course_id})'

            elif level.type == ElectionLevel.TYPE_STATE:
                if user.state is None:
                    eligible = False
                    reason = 'user-no-state'
                elif level.state_id == user.state_id:
                    eligible = True
                    reason = f'state-match ({user.state_id})'
                else:
                    eligible = False
                    reason = f'state-mismatch (level={level.state_id} user={user.state_id})'

            debug_reasons.append((level.id, level.type, eligible, reason))

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

        print(f"notify: user={user.id} email={user.email} tokens_count={len(tokens)} reasons={debug_reasons}")

        if tokens and user.email:
            subject = f"MWECAU Election Platform - New Election: {election.title}"
            message = (
                f"Dear {user.get_full_name()},\n\n"
                f"A new election is active: {election.title}\n"
                f"Description: {election.description or 'No description provided'}\n"
                f"Start Date: {election.start_date}\n"
                f"End Date: {election.end_date}\n\n"
                f"Your Voter Tokens:\n" +
                "\n".join([f"- {level_name}: {token}" for level_name, token in tokens]) +
                f"\n\nVote at the election platform.\n"
                f"Note: Keep your voter tokens secure and do not share them."
            )
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
                    recipient_list=[user.email],
                    fail_silently=False
                )
            except Exception as e:
                print(f"Failed to send election notification to {user.email}: {str(e)}")


@shared_task(queue='email_queue')
def send_vote_confirmation_email(user_id, election_id, level_id):
    """Send email confirmation after a user votes."""
    try:
        user = User.objects.get(id=user_id)
        election = Election.objects.get(id=election_id)
        level = ElectionLevel.objects.get(id=level_id)
        
        if not user.email:
            return
        
        subject = f"MWECAU Election Platform - Vote Confirmation: {election.title}"
        message = (
            f"Dear {user.get_full_name()},\n\n"
            f"Thank you for voting in the {election.title} ({level.name} level).\n"
            f"Your vote was recorded on {timezone.now()}.\n"
            f"View results after the election ends at the election platform."
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'xyztempo12345@tutamail.com',
            recipient_list=[user.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Error sending vote confirmation email: {e}")


@shared_task(queue='email_queue')
def send_election_starting_reminder(election_id):
    """Send reminder 5 minutes before election starts."""
    try:
        election = Election.objects.get(id=election_id)
        
        # Check if election is about to start
        time_until_start = election.start_date - timezone.now()
        if time_until_start > timedelta(minutes=10) or time_until_start < timedelta(minutes=0):
            return  # Too early or already started
        
        voters = User.objects.filter(is_verified=True, voter_id__isnull=False)
        
        for user in voters:
            if not user.email:
                continue
            
            subject = f"REMINDER: Election Starting Soon - {election.title}"
            message = (
                f"Dear {user.get_full_name()},\n\n"
                f"This is a reminder that the following election will start in approximately 5 minutes:\n\n"
                f"Election: {election.title}\n"
                f"Start Time: {election.start_date}\n"
                f"End Time: {election.end_date}\n\n"
                f"Make sure you are ready to cast your vote!\n"
                f"Log in to the election platform to participate.\n\n"
                f"Regards,\nMWECAU Election Commission"
            )
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
                    recipient_list=[user.email],
                    fail_silently=True
                )
            except Exception as e:
                print(f"Failed to send starting reminder to {user.email}: {e}")
                
    except Election.DoesNotExist:
        print(f"Election {election_id} not found for starting reminder")


@shared_task(queue='email_queue')
def send_non_voters_reminder(election_id):
    """Send reminder to voters who haven't voted yet - 30 minutes before election ends."""
    try:
        election = Election.objects.get(id=election_id)
        
        # Check if we're in the reminder window (30-60 minutes before end)
        time_until_end = election.end_date - timezone.now()
        if time_until_end > timedelta(minutes=60) or time_until_end < timedelta(minutes=0):
            return  # Too early or already ended
        
        # Get all voters with tokens for this election
        all_tokens = VoterToken.objects.filter(election=election).select_related('user')
        
        for token in all_tokens:
            # Skip if token is already used
            if token.is_used:
                continue
            
            user = token.user
            if not user.email:
                continue
            
            subject = f"URGENT: Election Ending Soon - {election.title}"
            message = (
                f"Dear {user.get_full_name()},\n\n"
                f"This is an urgent reminder that the following election will end in approximately 30 minutes:\n\n"
                f"Election: {election.title}\n"
                f"End Time: {election.end_date}\n\n"
                f"We notice you haven't cast your vote yet. Please log in to the platform immediately to participate.\n"
                f"This is your last chance to have your voice heard!\n\n"
                f"Your voter token is available in your dashboard.\n\n"
                f"Regards,\nMWECAU Election Commission"
            )
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
                    recipient_list=[user.email],
                    fail_silently=True
                )
            except Exception as e:
                print(f"Failed to send non-voter reminder to {user.email}: {e}")
                
    except Election.DoesNotExist:
        print(f"Election {election_id} not found for non-voter reminder")


@shared_task(queue='email_queue')
def send_custom_election_notification(election_id, custom_message):
    """Send custom notification from admin panel to all eligible voters."""
    try:
        election = Election.objects.get(id=election_id)
        
        # Get all voters with tokens for this election
        voters_with_tokens = User.objects.filter(
            voter_tokens__election=election,
            is_verified=True
        ).distinct()
        
        for user in voters_with_tokens:
            if not user.email:
                continue
            
            subject = f"Election Notification - {election.title}"
            message = (
                f"Dear {user.get_full_name()},\n\n"
                f"{custom_message}\n\n"
                f"Election: {election.title}\n"
                f"Start Date: {election.start_date}\n"
                f"End Date: {election.end_date}\n\n"
                f"Regards,\nMWECAU Election Commission"
            )
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
                    recipient_list=[user.email],
                    fail_silently=True
                )
            except Exception as e:
                print(f"Failed to send custom notification to {user.email}: {e}")
                
    except Election.DoesNotExist:
        print(f"Election {election_id} not found for custom notification")
