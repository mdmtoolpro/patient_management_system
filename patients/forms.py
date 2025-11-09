from django import forms
from .models import Patient, Visit, MedicalExamination
from phonenumber_field.formfields import PhoneNumberField

class PatientRegistrationForm(forms.ModelForm):
    phone = PhoneNumberField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '+251 9XXXXXXXX'
    }))
    
    class Meta:
        model = Patient
        fields = ('first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 
                 'address', 'emergency_contact', 'blood_group', 'allergies', 'medical_history')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': '2006-12-31'  # At least 18 years old
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'List any known allergies...'}),
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Previous medical conditions, surgeries, etc...'}),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if Patient.objects.filter(phone=phone).exists():
            raise forms.ValidationError("A patient with this phone number already exists.")
        return phone

class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ('assigned_doctor', 'symptoms')
        widgets = {
            'assigned_doctor': forms.Select(attrs={'class': 'form-select'}),
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Describe patient symptoms...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active doctors
        from users.models import User
        self.fields['assigned_doctor'].queryset = User.objects.filter(
            role=User.Role.DOCTOR, 
            is_active=True
        )

class MedicalExaminationForm(forms.ModelForm):
    class Meta:
        model = MedicalExamination
        fields = ('blood_pressure', 'temperature', 'heart_rate', 'weight', 'height', 'examination_notes')
        widgets = {
            'blood_pressure': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 120/80'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': '℃'
            }),
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'bpm'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'kg'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'cm'
            }),
            'examination_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed examination findings...'
            }),
        }