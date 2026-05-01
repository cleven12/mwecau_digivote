from rest_framework.throttling import UserRateThrottle


class VoteSubmitThrottle(UserRateThrottle):
    scope = 'vote_submit'
