from django.core.mail import send_mail
from django.conf import settings
from core.models import User
from .models import Election, ElectionLevel, VoterToken, Position
import uuid
from django.utils import timezone

def notify_voters_of_active_election(election_id):
    election = Election.objects.get(id=election_id)
    if not election.is_ongoing():
        return
    voters = User.objects.filter(is_verified=True, voter_id__isnull=False)
    for user in voters:
        tokens = []
        for level in election.levels.all():
            if (level.code == ElectionLevel.LEVEL_PRESIDENT or
                (level.code == ElectionLevel.LEVEL_COURSE and user.course and Position.objects.filter(election_level=level, course=user.course).exists()) or
                (level.code == ElectionLevel.LEVEL_STATE and user.state and Position.objects.filter(election_level=level, state=user.state).exists())):
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
        if tokens:
            subject = f"MWECAU Election Platform - New Election: {election.title}"
            message = (
                f"Dear {user.get_full_name()},\n\n"
                f"A new election is active: {election.title}\n"
                f"Description: {election.description or 'No description provided'}\n"
                f"Start Date: {election.start_date}\n"
                f"End Date: {election.end_date}\n\n"
                f"Your Voter Tokens:\n" + "\n".join([f"- {level_name}: {token}" for level_name, token in tokens]) +
                f"\nVote at: http://localhost:8000/api/election/vote/\n"
                f"Note: Keep your voter tokens secure and do not share them."
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=True
            )

def send_vote_confirmation_email(user_id, election_id, level_id):
    user = User.objects.get(id=user_id)
    election = Election.objects.get(id=election_id)
    level = ElectionLevel.objects.get(id=level_id)
    subject = f"MWECAU Election Platform - Vote Confirmation: {election.title}"
    message = (
        f"Dear {user.get_full_name()},\n\n"
        f"Thank you for voting in the {election.title} ({level.name} level).\n"
        f"Your vote was recorded on {timezone.now()}.\n"
        f"View results after the election ends at: http://localhost:8000/api/election/results/{election_id}/"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=True
    )