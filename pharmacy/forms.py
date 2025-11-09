from django import forms
from .models import Medicine, Prescription, PrescriptionItem

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ('medicine_id', 'name', 'generic_name', 'category', 'manufacturer', 
                 'description', 'quantity_in_stock', 'reorder_level', 'unit_price',
                 'dosage_form', 'strength', 'side_effects', 'contraindications', 'is_active')
        widgets = {
            'medicine_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'generic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dosage_form': forms.TextInput(attrs={'class': 'form-control'}),
            'strength': forms.TextInput(attrs={'class': 'form-control'}),
            'side_effects': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contraindications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ('notes',)
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional instructions for the pharmacist...'
            }),
        }

class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ('medicine', 'quantity', 'dosage', 'duration', 'instructions')
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-select medicine-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 500mg twice daily'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 7 days'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Special instructions for the patient...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active medicines with stock
        self.fields['medicine'].queryset = Medicine.objects.filter(
            is_active=True, 
            quantity_in_stock__gt=0
        )

class MedicineSearchForm(forms.Form):
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by medicine name, generic name, or ID...',
            'id': 'medicineSearch'
        })
    )

class DispenseForm(forms.Form):
    prescription_id = forms.CharField(widget=forms.HiddenInput())
    confirm_dispensing = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I confirm that I have dispensed all medicines correctly"
    )