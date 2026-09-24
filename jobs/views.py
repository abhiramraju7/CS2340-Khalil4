from django.shortcuts import render

from .models import Job


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
