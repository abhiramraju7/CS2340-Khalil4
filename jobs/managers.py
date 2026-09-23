from django.db import models


class JobQuerySet(models.QuerySet):
    """Queryset for Job, supplied by the moderation story.

    Public-facing views (search, map, recommendations) must use
    Job.objects.visible() so that administrator-removed postings disappear
    from the product without being deleted from the database.
    """

    def visible(self):
        from .models import Job
        return self.exclude(status=Job.STATUS_REMOVED)

    def removed(self):
        from .models import Job
        return self.filter(status=Job.STATUS_REMOVED)

    def flagged(self):
        from .models import Job
        return self.filter(status=Job.STATUS_FLAGGED)
