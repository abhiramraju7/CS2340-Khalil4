# Model contract — post this in Teams before anyone writes models

Kyle (admin stories 11 & 12) needs two things to exist. Everything else in
the admin panel is self-contained and will not touch your apps.

## 1. `accounts/models.py` — Profile (Kyle wrote it; Ridwan extends it)

Ridwan: your job-seeker profile story (#2) should add its fields to **this same
model** rather than creating a second one, so a user has one profile row.

```python
class Profile(models.Model):
    ROLE_SEEKER    = 'SEEKER'
    ROLE_RECRUITER = 'RECRUITER'
    ROLE_ADMIN     = 'ADMIN'
    ROLE_CHOICES = [(ROLE_SEEKER, 'Job Seeker'),
                    (ROLE_RECRUITER, 'Recruiter'),
                    (ROLE_ADMIN, 'Administrator')]

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,
                            default=ROLE_SEEKER)
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.CharField(max_length=255, blank=True)
    # Ridwan: headline / skills / education / links / privacy go here
```

A `post_save` signal creates a Profile for every new User, so
`user.profile` is always safe to read. Superusers are created as
administrators automatically.

**Check the role like this**, in views and templates:

```python
request.user.profile.role == Profile.ROLE_RECRUITER
# or the shorthands: profile.is_admin, profile.is_recruiter
```

## 2. `jobs/models.py` — the moderation fields (Adam owns this model)

Adam: build the real Job model however the posting story needs, but please keep
this block verbatim. Everything in it is what moderation acts on.

```python
class Job(models.Model):
    STATUS_ACTIVE  = 'ACTIVE'
    STATUS_FLAGGED = 'FLAGGED'
    STATUS_REMOVED = 'REMOVED'
    STATUS_CHOICES = [(STATUS_ACTIVE, 'Active'),
                      (STATUS_FLAGGED, 'Flagged'),
                      (STATUS_REMOVED, 'Removed')]

    posted_by  = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='posted_jobs')
    created_at = models.DateTimeField(auto_now_add=True)

    status         = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                      default=STATUS_ACTIVE)
    removal_reason = models.CharField(max_length=255, blank=True)
    moderated_at   = models.DateTimeField(null=True, blank=True)
    moderated_by   = models.ForeignKey(User, null=True, blank=True,
                                       on_delete=models.SET_NULL,
                                       related_name='moderated_jobs')

    objects = JobQuerySet.as_manager()   # from jobs/managers.py, Kyle supplies
```

Your model also needs `title`, `company` and `location` fields (any reasonable
definition) because the moderation queue displays them.

## 3. The one thing Kyle needs back from everyone

> **Every public-facing job query uses `Job.objects.visible()`, never
> `Job.objects.all()`.**

Removing a posting is a *soft delete*: it sets `status = REMOVED` rather than
deleting the row, so the action is reversible, the audit trail survives, and
applications attached to the posting are not orphaned. `visible()` is what
makes a removed posting actually disappear from the product.

This affects:

- **Abdur** — job search and filters (story 3)
- **Abhiram** — the job map (story 8)
- **Adam** — the recruiter's own listings, and the applicant pipeline (stories 1, 5)

```python
Job.objects.visible()                      # public listings
Job.objects.visible().filter(...)          # search, map, filters
Job.objects.all()                          # ONLY the moderation queue
```

If you forget, nothing crashes — removed spam just keeps showing up on the
live site, which is exactly what the story is supposed to prevent.
