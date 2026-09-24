from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from jobs.models import Job

from .models import AuditLog

PASSWORD = 'testpass123'


def make_user(username, role=Profile.ROLE_SEEKER):
    user = User.objects.create_user(username=username, password=PASSWORD)
    user.profile.role = role
    user.profile.save()
    return user


class AdminAccessTests(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.ROLE_ADMIN)
        self.seeker = make_user('seeker')

        self.urls = [
            reverse('admin_panel.dashboard'),
            reverse('admin_panel.user_list'),
            reverse('admin_panel.job_list'),
            reverse('admin_panel.audit_list'),
            reverse('admin_panel.user_detail', args=[self.seeker.id]),
        ]

    def test_anonymous_is_redirected_to_login(self):
        for url in self.urls:
            response = self.client.get(url)
            self.assertRedirects(response, reverse('accounts.login'))

    def test_seeker_is_redirected_home(self):
        self.client.login(username='seeker', password=PASSWORD)

        for url in self.urls:
            response = self.client.get(url)
            self.assertRedirects(response, reverse('home.index'))

    def test_admin_can_open_every_page(self):
        self.client.login(username='admin', password=PASSWORD)

        for url in self.urls:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_superuser_without_admin_role_still_has_access(self):
        superuser = User.objects.create_superuser(
            username='root', password=PASSWORD, email='',
        )
        superuser.profile.role = Profile.ROLE_SEEKER
        superuser.profile.save()

        self.client.login(username='root', password=PASSWORD)

        response = self.client.get(reverse('admin_panel.dashboard'))
        self.assertEqual(response.status_code, 200)


class RoleManagementTests(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.ROLE_ADMIN)
        self.other_admin = make_user('admin2', Profile.ROLE_ADMIN)
        self.seeker = make_user('seeker')
        self.client.login(username='admin', password=PASSWORD)

    def test_change_role_updates_profile_and_writes_one_audit_row(self):
        self.client.post(
            reverse('admin_panel.change_role', args=[self.seeker.id]),
            {'role': Profile.ROLE_RECRUITER},
        )

        self.seeker.profile.refresh_from_db()
        self.assertEqual(self.seeker.profile.role, Profile.ROLE_RECRUITER)

        entries = AuditLog.objects.filter(
            action=AuditLog.ACTION_ROLE_CHANGED,
            target_id=self.seeker.id,
        )
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries.first().actor, self.admin)

    def test_admin_cannot_demote_themselves(self):
        self.client.post(
            reverse('admin_panel.change_role', args=[self.admin.id]),
            {'role': Profile.ROLE_SEEKER},
        )

        self.admin.profile.refresh_from_db()
        self.assertEqual(self.admin.profile.role, Profile.ROLE_ADMIN)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_admin_cannot_suspend_themselves(self):
        self.client.post(
            reverse('admin_panel.toggle_suspend', args=[self.admin.id]),
            {'reason': 'oops'},
        )

        self.admin.profile.refresh_from_db()
        self.assertFalse(self.admin.profile.is_suspended)

    def test_last_admin_cannot_be_demoted(self):
        # Leave exactly one other administrator, then demote them.
        self.other_admin.profile.role = Profile.ROLE_SEEKER
        self.other_admin.profile.save()

        promoted = make_user('admin3', Profile.ROLE_ADMIN)
        self.client.logout()
        self.client.login(username='admin3', password=PASSWORD)

        # 'admin' is now the only other active administrator; demoting them
        # is fine, but then demoting the last one must be refused.
        self.client.post(
            reverse('admin_panel.change_role', args=[self.admin.id]),
            {'role': Profile.ROLE_SEEKER},
        )
        self.admin.profile.refresh_from_db()
        self.assertEqual(self.admin.profile.role, Profile.ROLE_SEEKER)

        # promoted is the last admin and cannot demote themselves either.
        self.client.post(
            reverse('admin_panel.change_role', args=[promoted.id]),
            {'role': Profile.ROLE_SEEKER},
        )
        promoted.profile.refresh_from_db()
        self.assertEqual(promoted.profile.role, Profile.ROLE_ADMIN)

    def test_last_admin_cannot_be_suspended(self):
        self.other_admin.profile.role = Profile.ROLE_SEEKER
        self.other_admin.profile.save()

        promoted = make_user('admin3', Profile.ROLE_ADMIN)
        self.client.logout()
        self.client.login(username='admin3', password=PASSWORD)

        self.client.post(
            reverse('admin_panel.change_role', args=[self.admin.id]),
            {'role': Profile.ROLE_SEEKER},
        )

        # promoted is now the only administrator left.
        response = self.client.post(
            reverse('admin_panel.toggle_suspend', args=[promoted.id]),
            {'reason': 'test'},
        )
        promoted.profile.refresh_from_db()
        self.assertFalse(promoted.profile.is_suspended)
        self.assertIsNotNone(response)

    def test_suspend_then_reinstate(self):
        url = reverse('admin_panel.toggle_suspend', args=[self.seeker.id])

        self.client.post(url, {'reason': 'Spamming recruiters'})
        self.seeker.profile.refresh_from_db()
        self.assertTrue(self.seeker.profile.is_suspended)
        self.assertEqual(
            self.seeker.profile.suspension_reason, 'Spamming recruiters'
        )

        self.client.post(url, {})
        self.seeker.profile.refresh_from_db()
        self.assertFalse(self.seeker.profile.is_suspended)
        self.assertEqual(self.seeker.profile.suspension_reason, '')

        self.assertEqual(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_USER_SUSPENDED
            ).count(),
            1,
        )
        self.assertEqual(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_USER_REINSTATED
            ).count(),
            1,
        )

    def test_get_request_does_not_change_state(self):
        self.client.get(
            reverse('admin_panel.change_role', args=[self.seeker.id]),
            {'role': Profile.ROLE_ADMIN},
        )

        self.seeker.profile.refresh_from_db()
        self.assertEqual(self.seeker.profile.role, Profile.ROLE_SEEKER)


class SuspensionEnforcementTests(TestCase):
    def setUp(self):
        self.seeker = make_user('seeker')

    def test_suspended_user_cannot_log_in(self):
        self.seeker.profile.is_suspended = True
        self.seeker.profile.save()

        self.client.post(
            reverse('accounts.login'),
            {'username': 'seeker', 'password': PASSWORD},
        )

        response = self.client.get(reverse('home.index'))
        self.assertFalse(response.context['user'].is_authenticated)

    def test_active_session_is_ended_when_user_is_suspended(self):
        self.client.login(username='seeker', password=PASSWORD)
        self.assertTrue(
            self.client.get(reverse('home.index'))
            .context['user'].is_authenticated
        )

        self.seeker.profile.is_suspended = True
        self.seeker.profile.save()

        response = self.client.get(reverse('home.index'))
        self.assertRedirects(response, reverse('accounts.login'))


class JobModerationTests(TestCase):
    def setUp(self):
        self.admin = make_user('admin', Profile.ROLE_ADMIN)
        self.recruiter = make_user('recruiter', Profile.ROLE_RECRUITER)
        self.job = Job.objects.create(
            title='Backend Engineer',
            company='Northwind',
            posted_by=self.recruiter,
        )
        self.client.login(username='admin', password=PASSWORD)

    def test_remove_without_reason_is_rejected(self):
        self.client.post(
            reverse('admin_panel.remove_job', args=[self.job.id]),
            {'reason': ''},
        )

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.STATUS_ACTIVE)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_remove_soft_deletes_and_hides_from_visible(self):
        self.client.post(
            reverse('admin_panel.remove_job', args=[self.job.id]),
            {'reason': 'Spam posting'},
        )

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.STATUS_REMOVED)
        self.assertEqual(self.job.removal_reason, 'Spam posting')
        self.assertEqual(self.job.moderated_by, self.admin)
        self.assertIsNotNone(self.job.moderated_at)

        # Soft delete: gone from public listings, still in the database.
        self.assertNotIn(self.job, Job.objects.visible())
        self.assertIn(self.job, Job.objects.all())

        self.assertEqual(
            AuditLog.objects.filter(
                action=AuditLog.ACTION_JOB_REMOVED
            ).count(),
            1,
        )

    def test_removed_job_absent_from_public_job_page(self):
        # follow=True so the success banner ("... has been removed") is
        # consumed here rather than leaking into the next page's messages.
        self.client.post(
            reverse('admin_panel.remove_job', args=[self.job.id]),
            {'reason': 'Spam posting'},
            follow=True,
        )

        response = self.client.get(reverse('jobs.index'))
        self.assertNotContains(response, 'Backend Engineer')

    def test_flag_then_restore(self):
        self.client.post(
            reverse('admin_panel.flag_job', args=[self.job.id]),
            {'reason': 'Needs a second look'},
        )
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.STATUS_FLAGGED)
        self.assertIn(self.job, Job.objects.visible())

        self.client.post(
            reverse('admin_panel.remove_job', args=[self.job.id]),
            {'reason': 'Confirmed spam'},
        )
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.STATUS_REMOVED)

        self.client.post(
            reverse('admin_panel.restore_job', args=[self.job.id]),
            {},
        )
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.STATUS_ACTIVE)
        self.assertEqual(self.job.removal_reason, '')
        self.assertIn(self.job, Job.objects.visible())

    def test_moderation_queue_shows_removed_jobs(self):
        self.client.post(
            reverse('admin_panel.remove_job', args=[self.job.id]),
            {'reason': 'Spam posting'},
        )

        response = self.client.get(reverse('admin_panel.job_list'))
        self.assertContains(response, 'Backend Engineer')

    def test_recruiter_cannot_moderate(self):
        self.client.logout()
        self.client.login(username='recruiter', password=PASSWORD)

        self.client.post(
            reverse('admin_panel.remove_job', args=[self.job.id]),
            {'reason': 'I do not like it'},
        )

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, Job.STATUS_ACTIVE)


class ProfileSignalTests(TestCase):
    def test_profile_created_for_every_user(self):
        user = User.objects.create_user(username='new', password=PASSWORD)
        self.assertEqual(user.profile.role, Profile.ROLE_SEEKER)

    def test_superuser_gets_admin_role(self):
        root = User.objects.create_superuser(
            username='root', password=PASSWORD, email='',
        )
        self.assertEqual(root.profile.role, Profile.ROLE_ADMIN)
