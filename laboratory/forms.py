from django import forms
from .models import LabTestRequest, LabTestType, TestResult

class LabTestRequestForm(forms.ModelForm):
    class Meta:
        model = LabTestRequest
        fields = ('test_type', 'doctor_notes')
        widgets = {
            'test_type': forms.Select(attrs={'class': 'form-select'}),
            'doctor_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any specific instructions for the lab...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active test types
        self.fields['test_type'].queryset = LabTestType.objects.filter(is_active=True)

class LabTestTypeForm(forms.ModelForm):
    class Meta:
        model = LabTestType
        fields = ('name', 'description', 'price', 'turnaround_time', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'turnaround_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TestResultForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = ('result_data', 'findings', 'interpretation')
        widgets = {
            'result_data': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter test results or detailed text...'
            }),
            'findings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Key findings from the test...'
            }),
            'interpretation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Medical interpretation of the results...'
            }),
        }

class LabTestAssignmentForm(forms.ModelForm):
    class Meta:
        model = LabTestRequest
        fields = ('assigned_to',)
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import User
        self.fields['assigned_to'].queryset = User.objects.filter(
            role=User.Role.LAB_TECH, 
            is_active=True
        )