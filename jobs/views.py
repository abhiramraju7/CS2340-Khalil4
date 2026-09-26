from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ApplicationStatusForm, JobForm
from .models import Application, Job


def index(request):
    template_data = {'title': 'Jobs', 'jobs': Job.objects.visible()}
    return render(request, 'jobs/index.html', {'template_data': template_data})


def _recruiter_required(request):
    return request.user.profile.is_recruiter


@login_required
def my_listings(request):
    if not _recruiter_required(request):
        messages.error(request, 'Only recruiters can manage job listings.')
        return redirect('jobs.index')
    jobs = Job.objects.visible().filter(posted_by=request.user)
    return render(request, 'jobs/my_listings.html', {'jobs': jobs})


@login_required
def create(request):
    if not _recruiter_required(request):
        messages.error(request, 'Only recruiters can post job listings.')
        return redirect('jobs.index')
    form = JobForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        job = form.save(commit=False)
        job.posted_by = request.user
        job.save()
        messages.success(request, 'Job listing posted.')
        return redirect('jobs.my_listings')
    return render(request, 'jobs/job_form.html', {'form': form, 'heading': 'Post a job'})


@login_required
def edit(request, job_id):
    job = get_object_or_404(Job.objects.visible(), id=job_id)
    if job.posted_by != request.user:
        return HttpResponseForbidden('You can only edit your own job listings.')
    form = JobForm(request.POST or None, instance=job)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Job listing updated.')
        return redirect('jobs.my_listings')
    return render(request, 'jobs/job_form.html', {'form': form, 'heading': 'Edit job listing', 'job': job})


@login_required
def pipeline(request, job_id):
    if not _recruiter_required(request):
        messages.error(request, 'Only recruiters can manage applicants.')
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
