from django import forms

from accounts.models import Profile


class RoleChangeForm(forms.Form):
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class ModerationForm(forms.Form):
    """Reason attached to a moderation action.

    Optional when flagging (a flag is a request for a second look), required
    when removing, so that a removal is always explainable to the recruiter
    whose posting was taken down.
    """

    reason = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reason (e.g. spam, duplicate posting, abusive language)',
        }),
    )

    def __init__(self, *args, **kwargs):
        self.reason_required = kwargs.pop('reason_required', False)
        super().__init__(*args, **kwargs)

        if self.reason_required:
            self.fields['reason'].required = True

    def clean_reason(self):
        reason = self.cleaned_data.get('reason', '').strip()

        if self.reason_required and not reason:
            raise forms.ValidationError(
                'A reason is required when removing a job posting.'
            )

        return reason
