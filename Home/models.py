from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
from django.utils import timezone
from django.conf import settings


class CustomUser(AbstractUser):
    ADMIN = 'admin'
    DOCTOR = 'doctor'
    PATIENT = 'patient'
    RECEPTIONIST = 'receptionist'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (DOCTOR, 'Doctor'),
        (PATIENT, 'Patient'),
        (RECEPTIONIST, 'Receptionist'),
    ]
    
    role = models.CharField(max_length=15, choices=ROLE_CHOICES)
   
    def __str__(self):
        return f"{self.username} ({self.role})"



class Department(models.Model):
    dep_name = models.CharField(max_length=255)
    dep_description = models.TextField()
    dep_image=models.ImageField(upload_to='dep_images')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.dep_name

class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,null=True)
    doc_name = models.CharField(max_length=255)
    dep_name=models.ForeignKey(Department,on_delete=models.CASCADE,related_name="doctor",null=True)
    doc_image=models.ImageField(upload_to='dep_images')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.doc_name
    
class Appointment(models.Model):
     STATUS_CHOICES = [
        ('Requested', 'Requested'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    
     PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
     ]
      
     patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'patient'})  # Link appointment to patient
     doctor = models.ForeignKey(Doctor,on_delete=models.CASCADE)  # Name of the doctor
     appointment_date = models.DateTimeField()  # When the appointment is scheduled
     reason = models.TextField()  # Reason for the appointment
     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Requested')
     payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='Pending')
     payment_id = models.CharField(max_length=100, blank=True, null=True)  # PayPal payment ID
     created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of when the appointment was created

     def __str__(self):
        return f"Appointment for {self.patient.username} with {self.doctor} on {self.appointment_date} (Status: {self.status})"


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_charge_id = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - ${self.amount}"

class PatientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile')
    profile_image = models.ImageField(upload_to='patient_profiles/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=3, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}'s Profile"
        
    def get_profile_image_url(self):
        if self.profile_image and hasattr(self.profile_image, 'url'):
            return self.profile_image.url
        return '/static/images/default-profile.png'  # Default image path

class ReceptionistProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='receptionist_profiles/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    shift = models.CharField(max_length=20, choices=[
        ('morning', 'Morning Shift'),
        ('afternoon', 'Afternoon Shift'),
        ('night', 'Night Shift'),
    ])
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.get_shift_display()}"
