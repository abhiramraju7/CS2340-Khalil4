from django.contrib.auth.models import User

from accounts.models import Profile


def count_active_admins(exclude_user_id=None):
    """Administrators who can still sign in (i.e. not suspended)."""
    admins = User.objects.filter(
        profile__role=Profile.ROLE_ADMIN,
        profile__is_suspended=False,
        is_active=True,
    )

    if exclude_user_id is not None:
        admins = admins.exclude(id=exclude_user_id)

    return admins.count()


def block_self_action(request, target_user):
    """Stop an administrator acting on their own account.

    One misclick would otherwise cost an admin their own access.
    """
    if request.user.id == target_user.id:
        return 'You cannot change your own role or account standing.'

    return None


def block_last_admin(target_user):
    """Stop the last remaining administrator being demoted or suspended.

    Without this, the platform can be left with nobody able to open the
    management pages and no way back in through the product itself.
    """
    profile = target_user.profile

    if profile.role != Profile.ROLE_ADMIN or profile.is_suspended:
        return None

    if count_active_admins(exclude_user_id=target_user.id) == 0:
        return (
            'This is the last active administrator. Promote another '
            'administrator before changing this account.'
        )

    return None
