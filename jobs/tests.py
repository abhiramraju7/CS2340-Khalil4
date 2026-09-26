from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from .models import Application, Job


class RecruiterApplicantPipelineTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user('recruiter', password='password')
        self.recruiter.profile.role = Profile.ROLE_RECRUITER
        self.recruiter.profile.save()
        self.other_recruiter = User.objects.create_user('other', password='password')
        self.other_recruiter.profile.role = Profile.ROLE_RECRUITER
        self.other_recruiter.profile.save()
        self.applicant = User.objects.create_user('applicant', password='password')
        self.job = Job.objects.create(title='Engineer', company='Example', posted_by=self.recruiter)
        self.application = Application.objects.create(
            job=self.job, applicant=self.applicant, cover_note='I would love to contribute.',
        )

    def test_recruiter_can_view_own_pipeline(self):
        self.client.login(username='recruiter', password='password')
        response = self.client.get(reverse('jobs.pipeline', args=[self.job.id]))
        self.assertContains(response, self.applicant.username)
        self.assertContains(response, 'I would love to contribute.')

    def test_recruiter_can_update_an_applicant_status(self):
        self.client.login(username='recruiter', password='password')
        response = self.client.post(reverse('jobs.application_status', args=[self.application.id]), {
            'status': Application.STATUS_INTERVIEW,
        })
        self.assertRedirects(response, reverse('jobs.pipeline', args=[self.job.id]))
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.STATUS_INTERVIEW)

    def test_recruiter_cannot_manage_another_recruiters_pipeline(self):
        other_job = Job.objects.create(title='Other', company='Elsewhere', posted_by=self.other_recruiter)
        self.client.login(username='recruiter', password='password')
        response = self.client.get(reverse('jobs.pipeline', args=[other_job.id]))
        self.assertEqual(response.status_code, 404)


class RecruiterJobListingTests(TestCase):
    def setUp(self):
        self.recruiter = User.objects.create_user('recruiter', password='password')
        self.recruiter.profile.role = Profile.ROLE_RECRUITER
        self.recruiter.profile.save()
        self.other_recruiter = User.objects.create_user('other', password='password')
        self.other_recruiter.profile.role = Profile.ROLE_RECRUITER
        self.other_recruiter.profile.save()
        self.seeker = User.objects.create_user('seeker', password='password')

    def test_recruiter_can_create_a_listing(self):
        self.client.login(username='recruiter', password='password')
        response = self.client.post(reverse('jobs.create'), {
            'title': 'Backend Engineer', 'company': 'Example Co',
            'location': 'Atlanta, GA', 'description': 'Build reliable services.',
        })
        self.assertRedirects(response, reverse('jobs.my_listings'))
        self.assertEqual(Job.objects.get(title='Backend Engineer').posted_by, self.recruiter)

    def test_non_recruiter_cannot_create_a_listing(self):
        self.client.login(username='seeker', password='password')
        response = self.client.get(reverse('jobs.create'))
        self.assertRedirects(response, reverse('jobs.index'))
        self.assertFalse(Job.objects.exists())

    def test_recruiter_can_edit_own_listing_but_not_another_recruiters(self):
        mine = Job.objects.create(title='Original', company='Example', posted_by=self.recruiter)
        other = Job.objects.create(title='Other', company='Elsewhere', posted_by=self.other_recruiter)
        self.client.login(username='recruiter', password='password')
        response = self.client.post(reverse('jobs.edit', args=[mine.id]), {
            'title': 'Updated', 'company': 'Example', 'location': '', 'description': '',
        })
        self.assertRedirects(response, reverse('jobs.my_listings'))
        mine.refresh_from_db()
        self.assertEqual(mine.title, 'Updated')
        response = self.client.get(reverse('jobs.edit', args=[other.id]))
        self.assertEqual(response.status_code, 403)
