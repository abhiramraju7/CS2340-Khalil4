from django import forms

from .models import Application, Job


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['status']


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'location', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }
