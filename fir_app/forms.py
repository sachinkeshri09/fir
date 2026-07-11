from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from .models import AccusedDetails, ComplaintDetails


# --- KEEP THESE AUTHENTICATION FORMS ---
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


# --- DASHBOARD FORMS ---
class ComplaintDetailsForm(forms.ModelForm):
    ID_PROOF_CHOICES = [
        ('', '--- Select ID Proof ---'),
        ('Aadhaar Card', 'Aadhaar Card'),
        ('PAN Card', 'PAN Card'),
        ('Voter ID', 'Voter ID'),
    ]

    INCIDENT_CHOICES = [
        ('', '--- Select Category ---'),
        ('Theft/Robbery', 'Theft / Robbery / Burglary'),
        ('Assault', 'Assault / Physical Violence'),
        ('Cybercrime', 'Cybercrime / Online Fraud'),
        ('Harassment', 'Harassment / Stalking'),
        ('Missing Person', 'Missing Person'),
        ('Property Damage', 'Vandalism / Property Damage'),
        ('Other', 'Other (Please specify below)'),
    ]

    LANGUAGE_CHOICES = [
        ('English', 'English'),
        ('Hindi', 'Hindi'),
    ]

    incident_type = forms.ChoiceField(
        choices=INCIDENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select mb-3', 'id': 'incident-select'})
    )
    language_preference = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        initial='English',
        widget=forms.Select(attrs={'class': 'form-select mb-3'})
    )
    other_incident_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control mb-3',
            'id': 'other-incident-input',
            'placeholder': 'Please specify the exact crime...'
        })
    )
    id_proof = forms.ChoiceField(
        choices=ID_PROOF_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    id_proof_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ID proof number'})
    )

    class Meta:
        model = ComplaintDetails
        fields = ['complainant_name', 'district', 'police_station', 'incident_date', 'incident_time', 'location', 'incident_type', 'language_preference', 'description', 'contact_number', 'email', 'id_proof', 'id_proof_number']
        widgets = {
            'complainant_name': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'police_station': forms.TextInput(attrs={'class': 'form-control'}),
            'incident_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'incident_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9876543210'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. name@example.com'}),
            'language_preference': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        incident_type = cleaned_data.get('incident_type')
        other_incident_type = cleaned_data.get('other_incident_type')

        if incident_type == 'Other' and not other_incident_type:
            self.add_error('other_incident_type', 'Please specify the incident type when selecting Other.')

        return cleaned_data

    def save(self, commit=True):
        complaint = super().save(commit=False)

        if self.cleaned_data.get('incident_type') == 'Other':
            complaint.incident_type = self.cleaned_data.get('other_incident_type', '').strip()

        if commit:
            complaint.save()
        return complaint


class AccusedDetailsForm(forms.ModelForm):
    class Meta:
        model = AccusedDetails
        fields = ['name', 'age', 'physical_description', 'relationship_to_victim']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank if unknown'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'physical_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'relationship_to_victim': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Neighbor, None'}),
        }