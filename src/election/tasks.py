
from datetime import timezone
import uuid
from django.core.mail import send_mail
from django.conf import settings
from core.models import User
from .models import Election, ElectionLevel, Position, VoterToken

def notify_voters_of_active_election(election_id):
    """Send email notifications with per-level VoterTokens when an election is activated."""
    election = Election.objects.get(id=election_id)
    if not election.is_ongoing():
        return

    # Get eligible voters (verified with voter_id)
    voters = User.objects.filter(is_verified=True, voter_id__isnull=False)
    
    for user in voters:
        tokens = []
        for level in election.levels.all():
            # Check eligibility per level
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
            # Send email with all eligible tokens
            subject = f"MWECAU Election Platform - New Election: {election.title}"
            message = (
                f"Dear {user.get_full_name()},\n\n"
                f"A new election is active: {election.title}\n"
                f"Description: {election.description or 'No description provided'}\n"
                f"Start Date: {election.start_date}\n"
                f"End Date: {election.end_date}\n\n"
                f"Your Voter Tokens:\n" +
                "\n".join([f"- {level_name}: {token}" for level_name, token in tokens]) +
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
    """Send email confirmation after a user votes."""
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


# v[01]
# from celery import shared_task
# from django.core.mail import send_mail
# from django.conf import settings
# from core.models import User
# import uuid
# from .models import Election, VoterToken, Position, ElectionLevel

# @shared_task(queue='email_queue')
# def notify_voters_of_active_election(election_id):
#     """Send email notifications to eligible voters when an election is activated.
#     # Filters voters by User.state for State Leader elections, includes VoterToken.
#     """
#     election = Election.objects.get(id=election_id)
#     if not election.is_active:
#         return  # Skip if election is no longer active
    
#     # Get positions and their election levels
#     positions = Position.objects.filter(election=election).select_related('election_level', 'state')
#     state_leader_positions = positions.filter(election_level__code=ElectionLevel.LEVEL_STATE)
    
#     # Collect eligible voters
#     eligible_voters = set()
#     for position in positions:
#         if position.election_level.code == ElectionLevel.LEVEL_STATE and position.state:
#             # State Leader: voters from specific state
#             voters = User.objects.filter(
#                 state=position.state,
#                 is_verified=True,
#                 voter_id__isnull=False
#             )
#             eligible_voters.update(voters)
#         elif position.election_level.code == ElectionLevel.LEVEL_PRESIDENT:
#             # President: all verified voters
#             voters = User.objects.filter(is_verified=True, voter_id__isnull=False)
#             eligible_voters.update(voters)
#         elif position.election_level.code == ElectionLevel.LEVEL_COURSE and position.course:
#             # Course Leader: voters from specific course
#             voters = User.objects.filter(
#                 course=position.course,
#                 is_verified=True,
#                 voter_id__isnull=False
#             )
#             eligible_voters.update(voters)
    
#     # Generate VoterTokens and send emails
#     for user in eligible_voters:
#         token, created = VoterToken.objects.get_or_create(
#             user=user,
#             election=election,
#             defaults={'token': uuid.uuid4()}
#         )
#         if not created and token.is_used:
#             continue  # Skip if token already used
        
#         # Send email with election details and token
#         subject = f"MWECAU Election Platform - New Election: {election.title}"
#         message = (
#             f"Dear {user.get_full_name()},\n\n"
#             f"A new election is active: {election.title}\n"
#             f"Description: {election.description or 'No description provided'}\n"
#             f"Start Date: {election.start_date}\n"
#             f"End Date: {election.end_date}\n"
#             f"Your Voter Token: {token.token}\n"
#             f"Vote at: http://localhost:8000/api/election/vote/\n"
#             f"Note: Keep your voter token secure and do not share it."
#         )
#         send_mail(
#             subject=subject,
#             message=message,
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[user.email],
#             fail_silently=True,
#         )