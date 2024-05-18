from django import forms

class AuthorRequestForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea)
