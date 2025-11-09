from django import forms
from allauth.account.forms import SignupForm, LoginForm
from .models import User

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30,
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Last Name'
        })
    )

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        # Remove the username field completely
        if 'username' in self.fields:
            del self.fields['username']

    def save(self, request):
        # Call the parent save method to create the user
        user = super(CustomSignupForm, self).save(request)
        
        # Add first_name and last_name
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        
        return user

class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        # Customize the login field
        self.fields['login'].label = 'Email'
        self.fields['login'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email address'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })