from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from .models import DirectMessage


class RecruiterMessagingTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user('recruiter', password='password')
        self.recruiter.profile.role = Profile.ROLE_RECRUITER
        self.recruiter.profile.save()
        self.candidate = User.objects.create_user('candidate', password='password')
        self.other_recruiter = User.objects.create_user('other', password='password')
        self.other_recruiter.profile.role = Profile.ROLE_RECRUITER
        self.other_recruiter.profile.save()

    def test_recruiter_can_message_a_candidate(self):
        self.client.login(username='recruiter', password='password')

        response = self.client.post(reverse('messaging.compose'), {
            'recipient': self.candidate.id,
            'body': 'Thanks for applying. Would you be available to talk?',
        })

        self.assertRedirects(response, reverse('messaging.inbox'))
        message = DirectMessage.objects.get()
        self.assertEqual(message.sender, self.recruiter)
        self.assertEqual(message.recipient, self.candidate)

    def test_recruiter_cannot_select_another_recruiter_as_a_candidate(self):
        self.client.login(username='recruiter', password='password')

        response = self.client.post(reverse('messaging.compose'), {
            'recipient': self.other_recruiter.id,
            'body': 'Not a valid recipient.',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(DirectMessage.objects.exists())

    def test_candidate_cannot_access_recruiter_messaging(self):
        self.client.login(username='candidate', password='password')

        response = self.client.get(reverse('messaging.inbox'))

        self.assertRedirects(response, reverse('jobs.index'))
