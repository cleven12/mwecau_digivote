from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from core.models import User
from .models import Election, ElectionLevel, Position, VoterToken
import uuid


def notify_voters_of_active_election(election_id):
    """Send email notifications with per-level VoterTokens when an election is activated."""
    election = Election.objects.get(id=election_id)
    if not election.is_ongoing():
        return

    voters = User.objects.filter(is_verified=True, voter_id__isnull=False)

    # Debug/logging: record counts
    print(f"notify_voters_of_active_election: election={election.id} voters_count={voters.count()}")

    for user in voters:
        tokens = []
        # For debugging: collect reasons for inclusion/exclusion per level
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
                # ensure expiry_date is timezone-aware and copied from election
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

        # Print debugging information for this user - helpful to trace misassigned emails
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
