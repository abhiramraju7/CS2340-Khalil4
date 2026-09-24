from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from accounts.models import Profile


def is_admin(user):
    """True for administrators.

    Superusers count so that a freshly created createsuperuser account can
    reach the dashboard before anybody has been promoted through the UI.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    profile = getattr(user, 'profile', None)

    return profile is not None and profile.role == Profile.ROLE_ADMIN


def admin_required(view):
    """Restrict a view to administrators.

    Non-admins are redirected with a message rather than shown a bare 403,
    which keeps the experience inside the product's own look and feel.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts.login')

        if not is_admin(request.user):
            messages.error(
                request,
                'You need administrator access to open that page.',
            )
            return redirect('home.index')

        return view(request, *args, **kwargs)

    return wrapper
