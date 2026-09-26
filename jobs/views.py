from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ApplicationStatusForm
from .models import Application, Job


def index(request):
    """STUB -- Abdur owns the real search/filter view.

    Note the use of Job.objects.visible(): removed postings must never
    appear in a public listing.
    """
    template_data = {}
    template_data['title'] = 'Jobs'
    template_data['jobs'] = Job.objects.visible()

    return render(
        request,
        'jobs/index.html',
        {'template_data': template_data},
    )


def _recruiter_required(request):
    if request.user.profile.is_recruiter:
        return True
    messages.error(request, 'Only recruiters can manage applicants.')
    return False


@login_required
def pipeline(request, job_id):
    if not _recruiter_required(request):
        return redirect('jobs.index')
    job = get_object_or_404(Job.objects.visible(), id=job_id, posted_by=request.user)
    applications = job.applications.select_related('applicant')
    return render(request, 'jobs/pipeline.html', {'job': job, 'applications': applications})


@login_required
def update_application_status(request, application_id):
    application = get_object_or_404(Application.objects.select_related('job'), id=application_id)
    if application.job.posted_by != request.user:
        return HttpResponseForbidden('You can only manage applicants for your own listings.')
    if request.method != 'POST':
        return redirect('jobs.pipeline', job_id=application.job_id)

    form = ApplicationStatusForm(request.POST, instance=application)
    if form.is_valid():
        form.save()
        messages.success(request, 'Applicant status updated.')
    else:
        messages.error(request, 'Please choose a valid applicant status.')
    return redirect('jobs.pipeline', job_id=application.job_id)
