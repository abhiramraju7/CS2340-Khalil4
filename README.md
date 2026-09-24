# CS2340-Khalil4 — Job Search Platform

CS 2340 Second Project. A Django web application where recruiters post and
manage job openings, job seekers discover and apply to them, and administrators
keep the platform fair and free of spam.

## Setup

```sh
python3.12 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python manage.py migrate
./venv/bin/python manage.py seed_demo      # demo users + job postings
./venv/bin/python manage.py runserver
```

Requires Python 3.10+ (Django 5.0). The macOS system Python 3.9 is too old.

## Apps

| App | Responsibility | Owner |
|---|---|---|
| `home` | Landing page | — |
| `accounts` | Signup, login, `Profile` (role + account standing) | Ridwan / Kyle |
| `jobs` | Job postings, search, filters, map | Adam / Abdur / Abhiram |
| `admin_panel` | User & role management, job moderation, audit log | Kyle |

**`accounts` and `jobs` are partly scaffolding.** See
[ADMIN_PANEL_README.md](ADMIN_PANEL_README.md) for what is real and what is a
placeholder waiting for its owner.

## Before writing models, read [MODEL_CONTRACT.md](MODEL_CONTRACT.md)

Two agreements the whole team depends on:

1. Profile fields go on the existing `accounts.Profile`, not a second model.
2. **Public job queries use `Job.objects.visible()`**, never `Job.objects.all()`.
   Removing a posting is a soft delete; `visible()` is what actually keeps
   removed spam off the live site.

## Tests

```sh
./venv/bin/python manage.py test
```

## Deployment

The app deploys to PythonAnywhere on SQLite. Before deploying, add the
PythonAnywhere domain to `ALLOWED_HOSTS` in `jobportal/settings.py` and set
`DEBUG = False`.

Per the project spec, a user story only counts as complete once it works on the
deployed site — local tests passing is not enough.
