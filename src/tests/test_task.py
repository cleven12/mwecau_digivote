import unittest
from celery import current_app, uuid
from election.tasks import notify_voters_of_active_election, send_vote_confirmation_email
from core.models import User
from election.models import Election, ElectionLevel, VoterToken
from django.utils import timezone
from datetime import timedelta

class ElectionTasksTestCase(unittest.TestCase):
    def setUp(self):
        self.user = User.objects.create(
            registration_number="T/DEG/2020/0003",
            email="neema@mail.com",
            is_verified=True,
            voter_id=str(uuid.uuid4()),
            course_id=1,
            state_id=1
        )
        self.level_president = ElectionLevel.objects.create(code="president", name="President")
        self.level_course = ElectionLevel.objects.create(code="course", name="Course Leader")
        self.election = Election.objects.create(
            title="2025 General Election",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            is_active=True
        )
        self.election.levels.add(self.level_president, self.level_course)

    def test_notify_voters(self):
        notify_voters_of_active_election.delay(self.election.id)
        tokens = VoterToken.objects.filter(user=self.user, election=self.election)
        self.assertEqual(tokens.count(), 2)  # One for President, one for Course
        self.assertFalse(tokens.first().is_used)
        self.assertEqual(tokens.first().expiry_date.date(), self.election.end_date.date())

    def test_vote_confirmation(self):
        token = VoterToken.objects.create(
            user=self.user,
            election=self.election,
            election_level=self.level_president,
            expiry_date=self.election.end_date
        )
        send_vote_confirmation_email.delay(self.user.id, self.election.id, self.level_president.id)
        # Check email in console or email service logs

if __name__ == "__main__":
    unittest.main()