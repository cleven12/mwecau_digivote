from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from core.models import User
from .models import Election, ElectionLevel, Position, VoterToken, Vote
import uuid


@shared_task(queue='email_queue')
def send_verification_email(user_id):
    """
    Send verification email to user when they are verified.
    Generates tokens for all active elections they're eligible for.
    """
    try:
        user = User.objects.get(id=user_id)
        
        if not user.email:
            print(f"User {user_id} has no email, skipping verification email")
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
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
            recipient_list=[user.email],
            fail_silently=False
        )
        print(f"Verification email sent to {user.email}")
    except User.DoesNotExist:
        print(f"User {user_id} not found")
    except Exception as e:
        print(f"Error sending verification email: {e}")


@shared_task(queue='email_queue')
def notify_voters_of_active_election(election_id):
    """
    Send email notifications with per-level VoterTokens when an election is activated.
    Creates tokens for all eligible voters and sends them via email.
    """
    try:
        election = Election.objects.get(id=election_id)
        
        if not election.is_active:
            print(f"Election {election_id} is not active, skipping notifications")
            return

        # Get all verified voters
        voters = User.objects.filter(is_verified=True, voter_id__isnull=False)
        
        print(f"notify_voters_of_active_election: election={election.id} voters_count={voters.count()}")

        successful = 0
        failed = 0
        
        for user in voters:
            tokens = []
            eligible_levels = []
            
            for level in election.levels.select_related('course', 'state').all():
                eligible = _check_eligibility(user, level)
                eligible_levels.append((level, eligible))
                
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

            if not user.email:
                continue

            if tokens:
                # Send email with tokens
                subject = f"MWECAU DigiVote - New Election: {election.title}"
                message = (
                    f"Dear {user.get_full_name()},\n\n"
                    f"A new election is now active: {election.title}\n"
                    f"Description: {election.description or 'No description provided'}\n"
                    f"Start Date: {election.start_date}\n"
                    f"End Date: {election.end_date}\n\n"
                    f"Your Voter Tokens:\n" +
                    "\n".join([f"- {level_name}: {token}" for level_name, token in tokens]) +
                    f"\n\nVote at the election platform during the voting period.\n"
                    f"Note: Keep your voter tokens secure and do not share them.\n"
                    f"Each token can only be used once.\n\n"
                    f"Regards,\nMWECAU Election Commission"
                )
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
                        recipient_list=[user.email],
                        fail_silently=False
                    )
                    successful += 1
                except Exception as e:
                    print(f"Failed to send election notification to {user.email}: {str(e)}")
                    failed += 1
        
        print(f"Election notification complete: {successful} sent, {failed} failed")
    except Election.DoesNotExist:
        print(f"Election {election_id} not found")
    except Exception as e:
        print(f"Error in notify_voters_of_active_election: {e}")


@shared_task(queue='email_queue')
def schedule_election_reminders(election_id):
    """
    Schedule reminder tasks for an election.
    These will be executed at the appropriate times.
    """
    try:
        election = Election.objects.get(id=election_id)
        
        now = timezone.now()
        
        # Schedule 5-minute pre-start reminder
        start_reminder_eta = election.start_date - timedelta(minutes=5)
        if start_reminder_eta > now:
            send_election_starting_reminder.apply_async(
                args=[election_id],
                eta=start_reminder_eta
            )
            print(f"Scheduled start reminder for election {election_id} at {start_reminder_eta}")
        
        # Schedule 30-minute pre-end reminder for non-voters
        end_reminder_eta = election.end_date - timedelta(minutes=30)
        if end_reminder_eta > now:
            send_non_voters_reminder.apply_async(
                args=[election_id],
                eta=end_reminder_eta
            )
            print(f"Scheduled non-voter reminder for election {election_id} at {end_reminder_eta}")
    except Election.DoesNotExist:
        print(f"Election {election_id} not found for scheduling reminders")
    except Exception as e:
        print(f"Error scheduling election reminders: {e}")


@shared_task(queue='email_queue')
def send_election_starting_reminder(election_id):
    """
    Send reminder 5 minutes before election starts.
    Notifies all voters with active tokens.
    """
    try:
        election = Election.objects.get(id=election_id)
        
        # Get all users with valid (unused) tokens for this election
        tokens = VoterToken.objects.filter(
            election=election,
            is_used=False,
            expiry_date__gt=timezone.now()
        ).select_related('user').distinct('user')
        
        successful = 0
        failed = 0
        
        for token in tokens:
            user = token.user
            if not user.email:
                continue
            
            subject = f"REMINDER: {election.title} - Election Starting Soon!"
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
                    fail_silently=False
                )
                successful += 1
            except Exception as e:
                print(f"Failed to send start reminder to {user.email}: {e}")
                failed += 1
        
        print(f"Start reminder sent for election {election_id}: {successful} sent, {failed} failed")
    except Election.DoesNotExist:
        print(f"Election {election_id} not found for start reminder")
    except Exception as e:
        print(f"Error in send_election_starting_reminder: {e}")


@shared_task(queue='email_queue')
def send_vote_confirmation_email(user_id, election_id, level_id):
    """
    Send congratulation email to user after they successfully vote.
    """
    try:
        user = User.objects.get(id=user_id)
        election = Election.objects.get(id=election_id)
        level = ElectionLevel.objects.get(id=level_id)
        
        if not user.email:
            print(f"User {user_id} has no email, skipping confirmation")
            return
        
        subject = f"MWECAU DigiVote - Vote Confirmation: {election.title}"
        message = (
            f"Dear {user.get_full_name()},\n\n"
            f"Thank you for participating in the {election.title}!\n\n"
            f"Your vote for the {level.name} level has been successfully recorded.\n"
            f"Time: {timezone.now()}\n\n"
            f"Your vote is secure, anonymous, and counts!\n"
            f"Results will be available after the election ends.\n\n"
            f"Regards,\nMWECAU Election Commission"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
            recipient_list=[user.email],
            fail_silently=False
        )
        print(f"Vote confirmation sent to {user.email} for election {election_id}, level {level_id}")
    except (User.DoesNotExist, Election.DoesNotExist, ElectionLevel.DoesNotExist) as e:
        print(f"Error sending vote confirmation: {e}")
    except Exception as e:
        print(f"Error in send_vote_confirmation_email: {e}")


@shared_task(queue='email_queue')
def send_non_voters_reminder(election_id):
    """
    Send urgent reminder to voters who haven't voted yet - 30 minutes before election ends.
    Includes details about which election levels they haven't participated in.
    """
    try:
        election = Election.objects.get(id=election_id)
        
        # Get all users with valid (unused) tokens for this election
        non_voted_tokens = VoterToken.objects.filter(
            election=election,
            is_used=False,
            expiry_date__gt=timezone.now()
        ).select_related('user', 'election_level').order_by('user')
        
        # Group by user
        user_levels_map = {}
        for token in non_voted_tokens:
            user = token.user
            level = token.election_level
            
            if user.id not in user_levels_map:
                user_levels_map[user.id] = {
                    'user': user,
                    'levels': []
                }
            user_levels_map[user.id]['levels'].append(level.name)
        
        successful = 0
        failed = 0
        
        for user_data in user_levels_map.values():
            user = user_data['user']
            levels = user_data['levels']
            
            if not user.email:
                continue
            
            levels_text = "\n".join([f"  - {level}" for level in levels])
            
            subject = f"URGENT: {election.title} - Voting Ending Soon!"
            message = (
                f"Dear {user.get_full_name()},\n\n"
                f"This is an URGENT reminder that the following election will end in approximately 30 minutes:\n\n"
                f"Election: {election.title}\n"
                f"End Time: {election.end_date}\n\n"
                f"You have not voted yet for these levels:\n"
                f"{levels_text}\n\n"
                f"This is your LAST CHANCE to have your voice heard!\n"
                f"Please log in to the election platform immediately to cast your vote.\n\n"
                f"Your voter tokens are available in your dashboard.\n"
                f"Each token can only be used once.\n\n"
                f"Regards,\nMWECAU Election Commission"
            )
            
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
                    recipient_list=[user.email],
                    fail_silently=False
                )
                successful += 1
            except Exception as e:
                print(f"Failed to send non-voter reminder to {user.email}: {e}")
                failed += 1
        
        print(f"Non-voter reminder sent for election {election_id}: {successful} sent, {failed} failed")
    except Election.DoesNotExist:
        print(f"Election {election_id} not found for non-voter reminder")
    except Exception as e:
        print(f"Error in send_non_voters_reminder: {e}")


@shared_task(queue='email_queue')
def send_custom_election_notification(election_id, custom_message):
    """
    Send custom notification from admin panel to all eligible voters.
    """
    try:
        election = Election.objects.get(id=election_id)
        
        # Get all voters with tokens for this election
        voters_with_tokens = User.objects.filter(
            voter_tokens__election=election,
            is_verified=True
        ).distinct()
        
        successful = 0
        failed = 0
        
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
                    fail_silently=False
                )
                successful += 1
            except Exception as e:
                print(f"Failed to send custom notification to {user.email}: {e}")
                failed += 1
        
        print(f"Custom notification sent for election {election_id}: {successful} sent, {failed} failed")
    except Election.DoesNotExist:
        print(f"Election {election_id} not found for custom notification")
    except Exception as e:
        print(f"Error in send_custom_election_notification: {e}")


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

