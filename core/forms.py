from django import forms
from .models import SystemConfig

class SystemConfigForm(forms.ModelForm):
    class Meta:
        model = SystemConfig
        fields = ('key', 'value', 'description', 'is_active')
        widgets = {
            'key': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class NotificationFilterForm(forms.Form):
    notification_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(Notification.NotificationType.choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_read = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All'),
            ('read', 'Read'),
            ('unread', 'Unread')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )