from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from jobs.models import Job

PASSWORD = 'demopass123'

USERS = [
    ('admin_kyle', Profile.ROLE_ADMIN, False),
    ('recruiter_dana', Profile.ROLE_RECRUITER, False),
    ('recruiter_omar', Profile.ROLE_RECRUITER, False),
    ('seeker_lin', Profile.ROLE_SEEKER, False),
    ('seeker_priya', Profile.ROLE_SEEKER, False),
    ('seeker_banned', Profile.ROLE_SEEKER, True),
]

JOBS = [
    ('Junior Backend Engineer', 'Northwind Systems', 'Atlanta, GA',
     'recruiter_dana', Job.STATUS_ACTIVE, ''),
    ('Frontend Developer Intern', 'Northwind Systems', 'Remote',
     'recruiter_dana', Job.STATUS_ACTIVE, ''),
    ('Data Analyst', 'Peachtree Analytics', 'Atlanta, GA',
     'recruiter_omar', Job.STATUS_ACTIVE, ''),
    ('Mobile Engineer', 'Peachtree Analytics', 'Savannah, GA',
     'recruiter_omar', Job.STATUS_ACTIVE, ''),
    ('!!! EARN $$$ FROM HOME !!!', 'Unverified', '',
     'recruiter_omar', Job.STATUS_FLAGGED, ''),
    ('Urgent hiring send resume to gmail', 'Unknown', '',
     'recruiter_dana', Job.STATUS_FLAGGED, ''),
    ('Crypto Recruiter (no experience)', 'Anonymous LLC', '',
     'recruiter_omar', Job.STATUS_REMOVED, 'Spam posting'),
    ('Site Reliability Engineer', 'Northwind Systems', 'Atlanta, GA',
     'recruiter_dana', Job.STATUS_ACTIVE, ''),
]


class Command(BaseCommand):
    help = 'Create demo users and job postings for the administrator demo.'

    def handle(self, *args, **options):
        accounts = {}

        for username, role, suspended in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': username + '@example.edu'},
            )

            if created:
                user.set_password(PASSWORD)
                user.save()

            user.profile.role = role
            user.profile.is_suspended = suspended
            user.profile.suspension_reason = (
                'Repeated abusive messages' if suspended else ''
            )
            user.profile.save()

            accounts[username] = user

        for title, company, location, poster, status, reason in JOBS:
            Job.objects.get_or_create(
                title=title,
                company=company,
                defaults={
                    'location': location,
                    'description': 'Seeded posting for the Sprint 1 demo.',
                    'posted_by': accounts[poster],
                    'status': status,
                    'removal_reason': reason,
                },
            )

        self.stdout.write(self.style.SUCCESS(
            'Seeded ' + str(len(USERS)) + ' users and '
            + str(len(JOBS)) + ' job postings.'
        ))
        self.stdout.write('Every demo account uses the password: ' + PASSWORD)
