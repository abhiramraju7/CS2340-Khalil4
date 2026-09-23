from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect
from django.urls import reverse


class SuspendedUserMiddleware:
    """Ends the session of any user an administrator has suspended.

    Blocking at login alone is not enough: a user who was already signed in
    when they were suspended would keep their session until it expired.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)

        if user is not None and user.is_authenticated:
            profile = getattr(user, 'profile', None)

            if profile is not None and profile.is_suspended:
                exempt = [
                    reverse('accounts.login'),
                    reverse('accounts.logout'),
                ]

                if request.path not in exempt:
                    auth_logout(request)
                    messages.error(
                        request,
                        'Your account has been suspended by an '
                        'administrator.',
                    )
                    return redirect('accounts.login')

        return self.get_response(request)
