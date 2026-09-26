from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import Profile
from .forms import DirectMessageForm
from .models import DirectMessage


def _candidate_users():
    return Profile.objects.filter(role=Profile.ROLE_SEEKER).select_related('user').order_by('user__username').values_list('user', flat=True)


@login_required
def inbox(request):
    if not request.user.profile.is_recruiter:
        messages.error(request, 'Only recruiters can message candidates.')
        return redirect('jobs.index')
    candidate_ids = _candidate_users()
    sent = DirectMessage.objects.filter(sender=request.user, recipient_id__in=candidate_ids).select_related('recipient')
    return render(request, 'messaging/inbox.html', {'messages_sent': sent})


@login_required
def compose(request):
    if not request.user.profile.is_recruiter:
        messages.error(request, 'Only recruiters can message candidates.')
        return redirect('jobs.index')
    candidates = request.user.__class__.objects.filter(id__in=_candidate_users()).order_by('username')
    form = DirectMessageForm(request.POST or None, candidates=candidates)
    if request.method == 'POST' and form.is_valid():
        message = form.save(commit=False)
        message.sender = request.user
        message.save()
        messages.success(request, 'Message sent to ' + message.recipient.username + '.')
        return redirect('messaging.inbox')
    return render(request, 'messaging/compose.html', {'form': form})
