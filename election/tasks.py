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
    
    for user in voters:
        tokens = []
        for level in election.levels.all():
            if (level.type == ElectionLevel.TYPE_PRESIDENT or
                (level.type == ElectionLevel.TYPE_COURSE and user.course and level.course == user.course) or
                (level.type == ElectionLevel.TYPE_STATE and user.state and level.state == user.state)):
                token, _ = VoterToken.objects.get_or_create(
                    user=user,
                    election=election,
                    election_level=level,
                    defaults={
                        'token': uuid.uuid4(),
                        'expiry_date': election.end_date
                    }
                )
                if not token.is_used:
                    tokens.append((level.name, str(token.token)))
        
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
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@mwecau.ac.tz',
                recipient_list=[user.email],
                fail_silently=True
            )


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
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@mwecau.ac.tz',
            recipient_list=[user.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Error sending vote confirmation email: {e}")
