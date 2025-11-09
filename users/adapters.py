from allauth.account.adapter import DefaultAccountAdapter
from django import forms
from .models import User

class CustomAccountAdapter(DefaultAccountAdapter):
    
    def save_user(self, request, user, form, commit=True):
        """
        Saves a new `User` instance using information provided in the
        signup form.
        """
        from allauth.account.utils import user_email, user_field
        
        data = form.cleaned_data
        email = data.get('email')
        user_email(user, email)
        
        # Set first_name and last_name
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        
        if 'password1' in data:
            user.set_password(data["password1"])
        else:
            user.set_unusable_password()
            
        self.populate_username(request, user)
        
        if commit:
            # Ability not to commit makes it easier to derive from
            # this adapter by adding
            user.save()
        return user

    def populate_username(self, request, user):
        """
        Override to set username to email since we're not using username
        """
        user.username = user.email