from django.contrib.auth.models import User
from django.db import models


class AuditLog(models.Model):
    """An append-only record of every administrator action.

    Admin power is only "fair and safe" if it is accountable, so each
    state-changing view in this app writes exactly one row here. This is also
    the data source for the Sprint 2 stories (CSV export for reporting, and
    reviewing reports submitted about users or job postings).
    """

    ACTION_ROLE_CHANGED = 'ROLE_CHANGED'
    ACTION_USER_SUSPENDED = 'USER_SUSPENDED'
    ACTION_USER_REINSTATED = 'USER_REINSTATED'
    ACTION_JOB_FLAGGED = 'JOB_FLAGGED'
    ACTION_JOB_REMOVED = 'JOB_REMOVED'
    ACTION_JOB_RESTORED = 'JOB_RESTORED'

    ACTION_CHOICES = [
        (ACTION_ROLE_CHANGED, 'Role changed'),
        (ACTION_USER_SUSPENDED, 'User suspended'),
        (ACTION_USER_REINSTATED, 'User reinstated'),
        (ACTION_JOB_FLAGGED, 'Job flagged'),
        (ACTION_JOB_REMOVED, 'Job removed'),
        (ACTION_JOB_RESTORED, 'Job restored'),
    ]

    TARGET_USER = 'USER'
    TARGET_JOB = 'JOB'

    TARGET_CHOICES = [
        (TARGET_USER, 'User'),
        (TARGET_JOB, 'Job posting'),
    ]

    actor = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name='admin_actions',
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES)
    target_id = models.IntegerField()
    target_label = models.CharField(max_length=255)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            str(self.created_at) + ' - ' + self.get_action_display()
            + ' - ' + self.target_label
        )

    @staticmethod
    def record(actor, action, target_type, target_id, target_label, reason=''):
        return AuditLog.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_label=target_label,
            reason=reason,
        )
