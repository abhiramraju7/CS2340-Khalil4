from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import Profile
from jobs.models import Job

from .decorators import admin_required
from .forms import ModerationForm, RoleChangeForm
from .guards import block_last_admin, block_self_action
from .models import AuditLog

PAGE_SIZE = 10


# ---------------------------------------------------------------- dashboard

@admin_required
def dashboard(request):
    template_data = {}
    template_data['title'] = 'Management'
    template_data['section'] = 'dashboard'

    template_data['role_counts'] = [
        (label, Profile.objects.filter(role=value).count())
        for value, label in Profile.ROLE_CHOICES
    ]
    template_data['suspended_count'] = Profile.objects.filter(
        is_suspended=True
    ).count()
    template_data['status_counts'] = [
        (label, Job.objects.filter(status=value).count())
        for value, label in Job.STATUS_CHOICES
    ]
    template_data['recent_actions'] = AuditLog.objects.all()[:5]

    return render(
        request,
        'admin_panel/dashboard.html',
        {'template_data': template_data},
    )


# ------------------------------------------------- story 11: users & roles

@admin_required
def user_list(request):
    search_term = request.GET.get('search', '').strip()
    role = request.GET.get('role', '')
    standing = request.GET.get('standing', '')

    users = User.objects.select_related('profile').order_by('username')

    if search_term:
        users = users.filter(
            Q(username__icontains=search_term)
            | Q(email__icontains=search_term)
        )

    if role:
        users = users.filter(profile__role=role)

    if standing == 'suspended':
        users = users.filter(profile__is_suspended=True)
    elif standing == 'active':
        users = users.filter(profile__is_suspended=False)

    paginator = Paginator(users, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))

    template_data = {}
    template_data['title'] = 'Manage Users'
    template_data['section'] = 'users'
    template_data['page'] = page
    template_data['search'] = search_term
    template_data['role'] = role
    template_data['standing'] = standing
    template_data['role_choices'] = Profile.ROLE_CHOICES

    return render(
        request,
        'admin_panel/users.html',
        {'template_data': template_data},
    )


@admin_required
def user_detail(request, id):
    target = get_object_or_404(
        User.objects.select_related('profile'),
        id=id,
    )

    template_data = {}
    template_data['title'] = 'User: ' + target.username
    template_data['section'] = 'users'
    template_data['target'] = target
    template_data['form'] = RoleChangeForm(
        initial={'role': target.profile.role}
    )
    template_data['posted_jobs'] = target.posted_jobs.all()
    template_data['history'] = AuditLog.objects.filter(
        target_type=AuditLog.TARGET_USER,
        target_id=target.id,
    )

    return render(
        request,
        'admin_panel/user_detail.html',
        {'template_data': template_data},
    )


@admin_required
def change_role(request, id):
    if request.method != 'POST':
        return redirect('admin_panel.user_detail', id=id)

    target = get_object_or_404(User, id=id)
    form = RoleChangeForm(request.POST)

    if not form.is_valid():
        messages.error(request, 'Please choose a valid role.')
        return redirect('admin_panel.user_detail', id=id)

    new_role = form.cleaned_data['role']
    old_role = target.profile.role

    if new_role == old_role:
        messages.info(request, 'That user already has this role.')
        return redirect('admin_panel.user_detail', id=id)

    error = block_self_action(request, target)

    if error is None and new_role != Profile.ROLE_ADMIN:
        error = block_last_admin(target)

    if error is not None:
        messages.error(request, error)
        return redirect('admin_panel.user_detail', id=id)

    target.profile.role = new_role
    target.profile.save()

    AuditLog.record(
        actor=request.user,
        action=AuditLog.ACTION_ROLE_CHANGED,
        target_type=AuditLog.TARGET_USER,
        target_id=target.id,
        target_label=target.username,
        reason=old_role + ' -> ' + new_role,
    )

    messages.success(
        request,
        target.username + ' is now a '
        + target.profile.get_role_display() + '.',
    )

    return redirect('admin_panel.user_detail', id=id)


@admin_required
def toggle_suspend(request, id):
    if request.method != 'POST':
        return redirect('admin_panel.user_detail', id=id)

    target = get_object_or_404(User, id=id)
    profile = target.profile

    error = block_self_action(request, target)

    if error is None and not profile.is_suspended:
        error = block_last_admin(target)

    if error is not None:
        messages.error(request, error)
        return redirect('admin_panel.user_detail', id=id)

    if profile.is_suspended:
        profile.is_suspended = False
        profile.suspension_reason = ''
        profile.save()

        AuditLog.record(
            actor=request.user,
            action=AuditLog.ACTION_USER_REINSTATED,
            target_type=AuditLog.TARGET_USER,
            target_id=target.id,
            target_label=target.username,
        )

        messages.success(request, target.username + ' has been reinstated.')
    else:
        reason = request.POST.get('reason', '').strip()

        profile.is_suspended = True
        profile.suspension_reason = reason
        profile.save()

        AuditLog.record(
            actor=request.user,
            action=AuditLog.ACTION_USER_SUSPENDED,
            target_type=AuditLog.TARGET_USER,
            target_id=target.id,
            target_label=target.username,
            reason=reason,
        )

        messages.success(request, target.username + ' has been suspended.')

    return redirect('admin_panel.user_detail', id=id)


# -------------------------------------------- story 12: moderate job posts

@admin_required
def job_list(request):
    search_term = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')

    # Deliberately Job.objects.all(): the moderation queue is the one place
    # that must still see removed postings.
    jobs = Job.objects.select_related('posted_by')

    if search_term:
        jobs = jobs.filter(
            Q(title__icontains=search_term)
            | Q(company__icontains=search_term)
        )

    if status:
        jobs = jobs.filter(status=status)

    paginator = Paginator(jobs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get('page'))

    template_data = {}
    template_data['title'] = 'Moderate Job Postings'
    template_data['section'] = 'jobs'
    template_data['page'] = page
    template_data['search'] = search_term
    template_data['status'] = status
    template_data['status_choices'] = Job.STATUS_CHOICES
    template_data['form'] = ModerationForm()

    return render(
        request,
        'admin_panel/jobs.html',
        {'template_data': template_data},
    )


def _moderate(request, id, new_status, action, success_message,
              reason_required=False):
    """Shared body of the three moderation actions."""
    if request.method != 'POST':
        return redirect('admin_panel.job_list')

    job = get_object_or_404(Job, id=id)
    form = ModerationForm(request.POST, reason_required=reason_required)

    if not form.is_valid():
        messages.error(
            request,
            'A reason is required when removing a job posting.',
        )
        return redirect('admin_panel.job_list')

    reason = form.cleaned_data['reason']

    job.status = new_status
    job.moderated_at = timezone.now()
    job.moderated_by = request.user

    if new_status == Job.STATUS_REMOVED:
        job.removal_reason = reason
    elif new_status == Job.STATUS_ACTIVE:
        job.removal_reason = ''

    job.save()

    AuditLog.record(
        actor=request.user,
        action=action,
        target_type=AuditLog.TARGET_JOB,
        target_id=job.id,
        target_label=job.title,
        reason=reason,
    )

    messages.success(request, success_message.format(title=job.title))

    return redirect('admin_panel.job_list')


@admin_required
def flag_job(request, id):
    return _moderate(
        request,
        id,
        Job.STATUS_FLAGGED,
        AuditLog.ACTION_JOB_FLAGGED,
        '"{title}" has been flagged for review.',
    )


@admin_required
def remove_job(request, id):
    # Soft delete: the posting leaves every public listing but stays in the
    # database, so the action is reversible and applications are not orphaned.
    return _moderate(
        request,
        id,
        Job.STATUS_REMOVED,
        AuditLog.ACTION_JOB_REMOVED,
        '"{title}" has been removed from the platform.',
        reason_required=True,
    )


@admin_required
def restore_job(request, id):
    return _moderate(
        request,
        id,
        Job.STATUS_ACTIVE,
        AuditLog.ACTION_JOB_RESTORED,
        '"{title}" has been restored.',
    )


# ---------------------------------------------------------------- audit log

@admin_required
def audit_list(request):
    action = request.GET.get('action', '')

    entries = AuditLog.objects.select_related('actor')

    if action:
        entries = entries.filter(action=action)

    paginator = Paginator(entries, 25)
    page = paginator.get_page(request.GET.get('page'))

    template_data = {}
    template_data['title'] = 'Audit Log'
    template_data['section'] = 'audit'
    template_data['page'] = page
    template_data['action'] = action
    template_data['action_choices'] = AuditLog.ACTION_CHOICES

    return render(
        request,
        'admin_panel/audit_log.html',
        {'template_data': template_data},
    )
