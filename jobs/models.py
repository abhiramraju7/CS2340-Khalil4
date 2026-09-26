from django.contrib.auth.models import User
from django.db import models

from .managers import JobQuerySet


class Job(models.Model):
    """STUB -- Adam owns the real Job model (story: post and edit job roles).

    Only the moderation contract below is load-bearing for admin_panel. The
    descriptive fields are placeholders so the moderation queue has something
    to render; replace them with Adam's version and keep the status block.
    """

    STATUS_ACTIVE = 'ACTIVE'
    STATUS_FLAGGED = 'FLAGGED'
    STATUS_REMOVED = 'REMOVED'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_FLAGGED, 'Flagged'),
        (STATUS_REMOVED, 'Removed'),
    ]

    # --- placeholder fields, owned by Adam ---
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    posted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posted_jobs',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- moderation contract, owned by admin_panel ---
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )
    removal_reason = models.CharField(max_length=255, blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='moderated_jobs',
    )

    objects = JobQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.id) + ' - ' + self.title

    @property
    def is_removed(self):
        return self.status == Job.STATUS_REMOVED


class Application(models.Model):
    STATUS_SUBMITTED = 'SUBMITTED'
    STATUS_REVIEWING = 'REVIEWING'
    STATUS_INTERVIEW = 'INTERVIEW'
    STATUS_REJECTED = 'REJECTED'
    STATUS_HIRED = 'HIRED'
    STATUS_CHOICES = [
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_REVIEWING, 'Reviewing'),
        (STATUS_INTERVIEW, 'Interview'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_HIRED, 'Hired'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    cover_note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['job', 'applicant'], name='one_application_per_job_seeker'),
        ]

    def __str__(self):
        return self.applicant.username + ' - ' + self.job.title
