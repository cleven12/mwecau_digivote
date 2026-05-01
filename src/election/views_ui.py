from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Prefetch
from django.utils import timezone
from django.http import Http404
from django.core.cache import cache
from asgiref.sync import sync_to_async
from .models import Election, ElectionLevel, Position, Candidate, VoterToken, Vote
from core.models import User


def _check_election_eligibility(user, election):
    """Check if user is eligible to vote in this election."""
    if not user.is_verified:
        return False, "not_verified"
    has_token = VoterToken.objects.filter(user=user, election=election).exists()
    if not has_token:
        return False, "no_token"
    return True, "eligible"


def _get_election_status(election):
    """Get election status badge info."""
    now = timezone.now()
    if election.has_ended:
        return {'status': 'ended', 'label': 'Ended', 'color': 'danger'}
    elif election.is_active:
        return {'status': 'active', 'label': 'Active', 'color': 'success'}
    elif election.start_date > now:
        return {'status': 'upcoming', 'label': 'Upcoming', 'color': 'info'}
    else:
        return {'status': 'pending', 'label': 'Pending', 'color': 'warning'}


@login_required
async def elections_list(request):
    """List all elections with prefetched user tokens — no N+1 queries."""
    user = request.user

    @sync_to_async
    def fetch_elections_data():
        user_tokens_qs = VoterToken.objects.filter(user=user)
        all_elections = list(
            Election.objects.prefetch_related(
                'levels',
                Prefetch(
                    'voter_tokens',
                    queryset=user_tokens_qs,
                    to_attr='user_voter_tokens'
                ),
            ).order_by('-start_date')
        )

        elections_data = []
        for election in all_elections:
            user_tokens = election.user_voter_tokens
            has_token = len(user_tokens) > 0

            if not user.is_verified:
                is_eligible, eligibility_reason = False, "not_verified"
            elif not has_token:
                is_eligible, eligibility_reason = False, "no_token"
            else:
                is_eligible, eligibility_reason = True, "eligible"

            has_voted = any(t.is_used for t in user_tokens)
            status_info = _get_election_status(election)

            elections_data.append({
                'election': election,
                'status_info': status_info,
                'is_eligible': is_eligible,
                'eligibility_reason': eligibility_reason,
                'has_voted': has_voted,
                'can_vote': is_eligible and election.is_active and not has_voted,
                'can_view_results': user.is_commissioner() or user.is_observer() or election.has_ended,
                'token_count': len(user_tokens),
            })
        return elections_data

    elections_data = await fetch_elections_data()

    active_elections   = [e for e in elections_data if e['status_info']['status'] == 'active']
    upcoming_elections = [e for e in elections_data if e['status_info']['status'] == 'upcoming']
    ended_elections    = [e for e in elections_data if e['status_info']['status'] == 'ended']

    context = {
        'active_elections': active_elections,
        'upcoming_elections': upcoming_elections,
        'ended_elections': ended_elections,
        'all_elections_count': len(elections_data),
        'user': user,
    }
    return render(request, 'election/elections_list.html', context)


@login_required
def election_vote(request, election_id):
    """Voting page — kept sync because write validation is complex."""
    election = get_object_or_404(Election, id=election_id)
    user = request.user
    now = timezone.now()

    if not election.is_ongoing():
        status_info = _get_election_status(election)
        messages.error(request, f"This election is {status_info['label'].lower()} and voting is not available.")
        return redirect('election:elections_list')

    is_eligible, eligibility_reason = _check_election_eligibility(user, election)
    if not is_eligible:
        if eligibility_reason == "not_verified":
            messages.error(request, "Your account is not verified. Please verify your account first.")
        elif eligibility_reason == "no_token":
            messages.error(request, "You are not eligible to vote in this election.")
        return redirect('election:elections_list')

    user_tokens = VoterToken.objects.filter(
        user=user,
        election=election
    ).select_related('election_level')

    if not user_tokens.exists():
        messages.error(request, "No voting tokens available for this election.")
        return redirect('election:elections_list')

    voting_levels = []
    for token in user_tokens:
        level = token.election_level
        positions = Position.objects.filter(election_level=level).prefetch_related(
            'candidates__user',
            'candidates__running_mate',
        )
        voting_levels.append({
            'token': token,
            'level': level,
            'positions': positions,
            'has_voted': token.is_used,
            'can_vote': not token.is_used and election.is_ongoing(),
        })

    all_voted = all(t['has_voted'] for t in voting_levels)

    context = {
        'election': election,
        'voting_levels': voting_levels,
        'all_voted': all_voted,
        'status_info': _get_election_status(election),
        'election_time_remaining': election.end_date - now if election.is_active else None,
    }
    return render(request, 'election/vote.html', context)


@login_required
async def election_results(request, election_id):
    """Results page — async with Redis caching. One DB query for all candidates."""
    try:
        election = await Election.objects.aget(id=election_id)
    except Election.DoesNotExist:
        raise Http404

    user = request.user
    can_view_results = (
        user.is_commissioner() or
        user.is_observer() or
        user.is_staff or
        election.has_ended
    )

    if not can_view_results:
        messages.error(request, "Results are not available yet. Please check back after the election ends.")
        return redirect('election:elections_list')

    cache_key = f'election_results:{election_id}'
    results = await cache.aget(cache_key)

    if results is None:
        @sync_to_async
        def compute_results():
            # One query — no nested loops hitting the DB
            all_candidates = list(
                Candidate.objects.filter(election=election)
                .select_related('user', 'position', 'position__election_level', 'running_mate')
                .annotate(vote_total=Count('votes'))
                .order_by('position__election_level_id', 'position_id', '-vote_total')
            )

            levels_map = {}
            for candidate in all_candidates:
                level = candidate.position.election_level
                position = candidate.position

                if level.id not in levels_map:
                    levels_map[level.id] = {
                        'level': level,
                        'positions': {},
                        'total_votes': 0,
                    }
                if position.id not in levels_map[level.id]['positions']:
                    levels_map[level.id]['positions'][position.id] = {
                        'position': position,
                        'candidates': [],
                        'total_votes': 0,
                    }

                levels_map[level.id]['positions'][position.id]['candidates'].append(candidate)
                levels_map[level.id]['positions'][position.id]['total_votes'] += candidate.vote_total
                levels_map[level.id]['total_votes'] += candidate.vote_total

            built = []
            for level_data in levels_map.values():
                level_positions = []
                for pos_data in level_data['positions'].values():
                    total = pos_data['total_votes']
                    candidate_results = []
                    for c in pos_data['candidates']:
                        pct = (c.vote_total / total * 100) if total > 0 else 0
                        candidate_results.append({
                            'candidate': c,
                            'vote_count': c.vote_total,
                            'percentage': round(pct, 2),
                        })
                    level_positions.append({
                        'position': pos_data['position'],
                        'candidates': candidate_results,
                        'total_votes': total,
                    })
                built.append({
                    'level': level_data['level'],
                    'positions': level_positions,
                    'total_votes': level_data['total_votes'],
                })
            return built

        results = await compute_results()
        timeout = 3600 if election.has_ended else 30
        await cache.aset(cache_key, results, timeout=timeout)

    status_info = _get_election_status(election)
    context = {
        'election': election,
        'results': results,
        'status_info': status_info,
        'is_results_final': election.has_ended,
        'can_view_results': can_view_results,
        'view_permission_reason': (
            'admin' if user.is_staff else
            'commissioner' if user.is_commissioner() else
            'observer' if user.is_observer() else
            'election_ended'
        ),
    }
    return render(request, 'election/results.html', context)


@login_required
def submit_vote(request, election_id):
    """Process vote submission — sync, handles complex write validation."""
    if request.method != 'POST':
        return redirect('election:vote', election_id=election_id)

    election = get_object_or_404(Election, id=election_id)

    try:
        token_id    = request.POST.get('token_id')
        candidate_id = request.POST.get('candidate_id')

        token     = get_object_or_404(VoterToken, id=token_id, user=request.user)
        candidate = get_object_or_404(Candidate, id=candidate_id)

        if token.is_used:
            messages.error(request, "This token has already been used.")
            return redirect('election:vote', election_id=election_id)

        if not election.is_ongoing():
            messages.error(request, "Election is not active.")
            return redirect('election:vote', election_id=election_id)

        if candidate.position.election_level != token.election_level:
            messages.error(request, "Invalid vote selection.")
            return redirect('election:vote', election_id=election_id)

        Vote.objects.create(token=token, candidate=candidate)
        token.mark_as_used()

        # Invalidate cached results so next view shows updated counts
        cache.delete(f'election_results:{election_id}')

        messages.success(request, f"Your vote for {candidate.position.title} has been recorded successfully!")

    except Exception as e:
        messages.error(request, f"Error submitting vote: {str(e)}")

    return redirect('election:vote', election_id=election_id)
