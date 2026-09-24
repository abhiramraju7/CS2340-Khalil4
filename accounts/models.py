from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """Per-user role and account standing.

    Owned by the admin_panel stories (manage users and roles). Ridwan's
    job-seeker profile fields (headline, skills, education, links, privacy)
    belong on this same model -- add them below the fields declared here.
    """

    ROLE_SEEKER = 'SEEKER'
    ROLE_RECRUITER = 'RECRUITER'
    ROLE_ADMIN = 'ADMIN'

    ROLE_CHOICES = [
        (ROLE_SEEKER, 'Job Seeker'),
        (ROLE_RECRUITER, 'Recruiter'),
        (ROLE_ADMIN, 'Administrator'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_SEEKER,
    )
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return str(self.user.username) + ' - ' + self.get_role_display()

    @property
    def is_admin(self):
        return self.role == Profile.ROLE_ADMIN

    @property
    def is_recruiter(self):
        return self.role == Profile.ROLE_RECRUITER
