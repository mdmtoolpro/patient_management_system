from django import forms
from .models import Payment, Invoice

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ('payment_type', 'payment_method', 'amount', 'notes')
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': 'readonly'  # Amount is calculated automatically
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any additional payment notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set amount based on context (will be set in view)
        if self.instance and self.instance.amount:
            self.fields['amount'].widget.attrs['value'] = self.instance.amount

class RegistrationPaymentForm(forms.ModelForm):
    """Specific form for registration fee payment"""
    class Meta:
        model = Payment
        fields = ('payment_method', 'notes')
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Payment notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].initial = Payment.PaymentMethod.CASH

class LabTestPaymentForm(forms.ModelForm):
    """Specific form for lab test payment"""
    class Meta:
        model = Payment
        fields = ('payment_method', 'notes')
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

class MedicinePaymentForm(forms.ModelForm):
    """Specific form for medicine payment"""
    class Meta:
        model = Payment
        fields = ('payment_method', 'notes')
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ('due_date', 'discount_amount', 'tax_amount')
        widgets = {
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }

class PaymentSearchForm(forms.Form):
    patient_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Patient ID...'
        })
    )
    
    payment_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Payment ID...'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )