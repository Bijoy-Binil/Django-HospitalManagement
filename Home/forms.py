# forms.py
from django import forms
from .models import *

class DoctorRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    doc_name = forms.CharField(max_length=255, required=True, label="Doctor Name")
    dep_name = forms.ModelChoiceField(queryset=Department.objects.all(), required=True, label="Department")
    doc_image = forms.ImageField(required=False, label="Profile Image")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'doctor'
        
        if commit:
            user.save()
            # Create the associated Doctor instance
            doctor = Doctor.objects.create(
                user=user,
                doc_name=self.cleaned_data['doc_name'],
                dep_name=self.cleaned_data['dep_name'],
                doc_image=self.cleaned_data.get('doc_image')
            )
            print(f"Created doctor profile for {user.username}")
        return user


class PatientRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    profile_image = forms.ImageField(required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    blood_group = forms.ChoiceField(choices=[
        ('', 'Select Blood Group'),
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ], required=False)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'confirm_password', 'first_name', 'last_name', 
                 'profile_image', 'phone_number', 'address', 'date_of_birth', 'blood_group']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'patient'
        
        if commit:
            user.save()
            
            # Create or update patient profile
            profile, created = PatientProfile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.address = self.cleaned_data.get('address', '')
            profile.date_of_birth = self.cleaned_data.get('date_of_birth')
            profile.blood_group = self.cleaned_data.get('blood_group', '')
            
            if self.cleaned_data.get('profile_image'):
                profile.profile_image = self.cleaned_data.get('profile_image')
                
            profile.save()
            
        return user



class ReceptionistRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    profile_image = forms.ImageField(required=False)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    shift = forms.ChoiceField(choices=[
        ('morning', 'Morning Shift (6 AM - 2 PM)'),
        ('afternoon', 'Afternoon Shift (2 PM - 10 PM)'),
        ('night', 'Night Shift (10 PM - 6 AM)'),
    ], required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'confirm_password', 'first_name', 'last_name',
                 'profile_image', 'phone_number', 'address', 'date_of_birth', 'shift']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.role = 'receptionist'
        
        if commit:
            user.save()
            
            # Create or update receptionist profile
            profile, created = ReceptionistProfile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.address = self.cleaned_data.get('address', '')
            profile.date_of_birth = self.cleaned_data.get('date_of_birth')
            profile.shift = self.cleaned_data.get('shift')
            
            if self.cleaned_data.get('profile_image'):
                profile.profile_image = self.cleaned_data.get('profile_image')
                
            profile.save()
            
        return user

class ReceptionistProfileForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control-file'}))
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    shift = forms.ChoiceField(choices=[
        ('morning', 'Morning Shift (6 AM - 2 PM)'),
        ('afternoon', 'Afternoon Shift (2 PM - 10 PM)'),
        ('night', 'Night Shift (10 PM - 6 AM)'),
    ], required=True)
    emergency_contact_name = forms.CharField(max_length=100, required=False)
    emergency_contact_number = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = ReceptionistProfile
        fields = ['profile_image', 'phone_number', 'address', 'date_of_birth', 'shift',
                 'emergency_contact_name', 'emergency_contact_number']

class DateInput(forms.DateInput):
    input_type='date'


class AppointmentForm(forms.ModelForm):
    dep_name = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label="Department",
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Department"
    )
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'reason']
        widgets = {
            'appointment_date': DateInput(),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = Doctor.objects.all().select_related('dep_name')
        self.fields['doctor'].label_from_instance = lambda obj: f"{obj.doc_name} ({obj.dep_name.dep_name if obj.dep_name else 'No Department'})"


class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status']
        widgets = {
            'status': forms.RadioSelect(choices=Appointment.STATUS_CHOICES),
        }        

class PaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    stripe_token = forms.CharField()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }

class PatientProfileForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control-file'}))
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    blood_group = forms.ChoiceField(choices=[
        ('', 'Select Blood Group'),
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ], required=False)
    emergency_contact_name = forms.CharField(max_length=100, required=False)
    emergency_contact_number = forms.CharField(max_length=15, required=False)
    allergies = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    medical_conditions = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    class Meta:
        model = PatientProfile
        fields = ['profile_image', 'phone_number', 'address', 'date_of_birth', 'blood_group',
                 'emergency_contact_name', 'emergency_contact_number', 'allergies', 'medical_conditions']
