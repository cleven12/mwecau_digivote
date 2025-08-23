from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from core.models import User
import uuid
from .models import Election, VoterToken, Position, ElectionLevel

@shared_task(queue='email_queue')
def notify_voters_of_active_election(election_id):
    """Send email notifications to eligible voters when an election is activated.
    # Filters voters by User.state for State Leader elections, includes VoterToken.
    """
    election = Election.objects.get(id=election_id)
    if not election.is_active:
        return  # Skip if election is no longer active
    
    # Get positions and their election levels
    positions = Position.objects.filter(election=election).select_related('election_level', 'state')
    state_leader_positions = positions.filter(election_level__code=ElectionLevel.LEVEL_STATE)
    
    # Collect eligible voters
    eligible_voters = set()
    for position in positions:
        if position.election_level.code == ElectionLevel.LEVEL_STATE and position.state:
            # State Leader: voters from specific state
            voters = User.objects.filter(
                state=position.state,
                is_verified=True,
                voter_id__isnull=False
            )
            eligible_voters.update(voters)
        elif position.election_level.code == ElectionLevel.LEVEL_PRESIDENT:
            # President: all verified voters
            voters = User.objects.filter(is_verified=True, voter_id__isnull=False)
            eligible_voters.update(voters)
        elif position.election_level.code == ElectionLevel.LEVEL_COURSE and position.course:
            # Course Leader: voters from specific course
            voters = User.objects.filter(
                course=position.course,
                is_verified=True,
                voter_id__isnull=False
            )
            eligible_voters.update(voters)
    
    # Generate VoterTokens and send emails
    for user in eligible_voters:
        token, created = VoterToken.objects.get_or_create(
            user=user,
            election=election,
            defaults={'token': uuid.uuid4()}
        )
        if not created and token.is_used:
            continue  # Skip if token already used
        
        # Send email with election details and token
        subject = f"MWECAU Election Platform - New Election: {election.title}"
        message = (
            f"Dear {user.get_full_name()},\n\n"
            f"A new election is active: {election.title}\n"
            f"Description: {election.description or 'No description provided'}\n"
            f"Start Date: {election.start_date}\n"
            f"End Date: {election.end_date}\n"
            f"Your Voter Token: {token.token}\n"
            f"Vote at: http://localhost:8000/api/election/vote/\n"
            f"Note: Keep your voter token secure and do not share it."
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=True,
        )