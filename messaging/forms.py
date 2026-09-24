from django import forms

from .models import DirectMessage


class DirectMessageForm(forms.ModelForm):
    class Meta:
        model = DirectMessage
        fields = ['recipient', 'body']
        widgets = {'body': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write a message...'})}

    def __init__(self, *args, candidates, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recipient'].queryset = candidates
