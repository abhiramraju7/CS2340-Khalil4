# admin_panel — drop-in instructions

Kyle's Sprint 1 stories:

- **Story 11** — As an Administrator, I want to manage users and roles so the
  platform remains fair and safe.
- **Story 12** — As an Administrator, I want to moderate or remove job posts so
  the platform stays free of spam or abuse.

This sandbox is **not** the team repo. It is a throwaway harness so the admin
work could start before the shared Django skeleton existed. When the real
skeleton lands, only two directories move across.

## What is Kyle's, and what is scaffolding

| Path | Status |
|---|---|
| `admin_panel/` | **Kyle's work.** Copy across as-is. |
| `accounts/models.py`, `signals.py`, `apps.py` | **Kyle's work.** Merge into the real accounts app. |
| `jobs/managers.py` | **Kyle's work.** Hand to Adam. |
| `jobs/models.py`, `jobs/views.py` | **Stub.** Adam owns the real ones. Delete. |
| `accounts/views.py`, `forms.py`, `urls.py`, templates | **Stub.** Ridwan owns signup/login. Keep only the suspended-account check in `login()`. |
| `home/`, `jobportal/`, `base.html` | **Stub.** Whoever builds the skeleton owns these. Delete. |

## Merge steps

1. Copy `admin_panel/` into the project root (excluding `admin_panel/migrations/`
   — regenerate those against the real schema).
2. Merge `accounts/models.py` (Profile), `accounts/signals.py`, and the
   `ready()` hook in `accounts/apps.py`.
3. Give `jobs/managers.py` to Adam; confirm `objects = JobQuerySet.as_manager()`
   is on the real `Job`.
4. `settings.py`:
   - add `'admin_panel'` to `INSTALLED_APPS`
   - add `'admin_panel.middleware.SuspendedUserMiddleware'` to `MIDDLEWARE`,
     **after** `MessageMiddleware` (it raises messages, so message storage has
     to be initialised first)
   - set `LOGIN_URL = 'accounts.login'`
   - add the PythonAnywhere domain to `ALLOWED_HOSTS`
5. `jobportal/urls.py`: `path('manage/', include('admin_panel.urls'))`
6. `python manage.py makemigrations && python manage.py migrate`
7. `python manage.py test admin_panel`

If the real accounts app already has users before Profile exists, add a data
migration that backfills a Profile row for each of them — the signal only fires
for newly created users.

## Assumptions baked into admin_panel

It expects these URL names to exist, which is the team's naming convention
anyway (`app.view`, as in Project 1):

- `home.index`
- `accounts.login`, `accounts.logout`
- `jobs.index`

And it expects `base.html` to provide a `{% block content %}` and render
`{% for message in messages %}`. Nothing else.

## Running the sandbox

```sh
PY=/Users/kylezhou/CS2340/Proj1/venv/bin/python   # Django 5.0.14
$PY manage.py migrate
$PY manage.py seed_demo
$PY manage.py runserver
```

`seed_demo` creates 6 users and 8 job postings across all three statuses.
Every demo account uses the password `demopass123`:

| Account | Role |
|---|---|
| `admin_kyle` | Administrator |
| `recruiter_dana`, `recruiter_omar` | Recruiter |
| `seeker_lin`, `seeker_priya` | Job Seeker |
| `seeker_banned` | Job Seeker, already suspended |

## Demo script (both stories, ~3 minutes)

Sign in as `admin_kyle`, go to **Manage**.

**Story 11 — users and roles**

1. `/manage/users/` — search for `seeker`, filter by role, filter by standing.
2. Open `seeker_lin` → change role to Recruiter → the banner and the role update.
3. Suspend `seeker_priya` with a reason.
4. In a private window, try to log in as `seeker_priya` → refused.
5. Try to demote yourself → refused, with an explanation.
6. Show `/manage/audit/`: every one of those actions is recorded, with who and why.

**Story 12 — moderating job postings**

1. `/jobs/` — note the spam posting is live.
2. `/manage/jobs/` — filter to Flagged; flag one posting for review.
3. Remove the spam posting. Try it with an empty reason first → refused.
4. `/jobs/` — the posting is gone.
5. `/manage/jobs/` — the posting is still here, marked Removed, reason attached.
6. Restore it → it reappears on `/jobs/`.
7. `/manage/audit/` — flag, remove and restore are all logged.

The point to make about the design: **removal is a soft delete.** The row stays,
so the action is reversible, the audit trail survives, and any applications
attached to the posting are not orphaned. `Job.objects.visible()` is what keeps
removed postings out of every public view.

## Tests

`python manage.py test admin_panel` — 21 tests covering access control for
anonymous / seeker / recruiter / admin / superuser, role changes and their audit
rows, the self-action and last-admin guard rails, suspension at login and
mid-session, and the full flag → remove → restore cycle including the
`visible()` / `all()` split.
