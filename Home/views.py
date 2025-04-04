from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import Http404, JsonResponse
from django.views import View
from .models import *
from .decorators import role_required
from .forms import *
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Max
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from datetime import datetime, timedelta
from django.db.models import Count
from decimal import Decimal
# Create your views here.

# <==============Login View======================>
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            print(f"User {user.username} authenticated successfully with role: {user.role}")
            
            # Redirect based on the user role
            if user.role == "admin":
                return redirect("Home:home")
            elif user.role == "doctor":
                # Check if doctor profile exists
                try:
                    doctor = Doctor.objects.get(user=user)
                    print(f"Doctor profile found for {user.username}")
                except Doctor.DoesNotExist:
                    print(f"No doctor profile found for {user.username}")
                    # Create a basic doctor profile if missing
                    if Department.objects.exists():
                        doctor = Doctor.objects.create(
                            user=user,
                            doc_name=f"Dr. {user.first_name} {user.last_name}" if user.first_name else user.username,
                            dep_name=Department.objects.first()
                        )
                        print(f"Created doctor profile for {user.username}")
                return redirect("Home:doctor_dashboard")
            elif user.role == "patient":
                return redirect("Home:patient_dashboard")
            elif user.role == "receptionist":
                return redirect("Home:receptionist_MainDashboard")
        else:
            print(f"Failed login attempt for username: {username}")
            return render(request, "login.html", {"error": "Invalid credentials"})

    return render(request, "login.html")


# <==============End Login View===================>


# <==============Registration===================>
def register_doctor(request):
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            print(f"Doctor registered successfully: {user.username}")
            return redirect('Home:login')
        else:
            print("Form errors:", form.errors)  # For debugging
    else:
        form = DoctorRegistrationForm()
    return render(request, 'registration/register_doctor.html', {'form': form})


def register_patient(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            auth_login(request, user)
            messages.success(request, "Registration successful! Welcome to our hospital management system.")
            return redirect('Home:patient_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PatientRegistrationForm()
    return render(request, 'registration/register_patient.html', {'form': form})


def register_receptionist(request):
    if request.method == 'POST':
        form = ReceptionistRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('Home:home')  # Redirect to the login page after successful registration
    else:
        form = ReceptionistRegistrationForm()
    return render(request, 'registration/register_receptionist.html', {'form': form})

# <==============End Registration===================>

# <==============Login Required For Dashboard======================>
@login_required
def admin_dashboard(request):
    return render(request, "admin_dashboard.html", {"user": request.user})

@login_required
def doctor_dashboard(request):
    print(f"Doctor dashboard accessed by user: {request.user.username}, role: {request.user.role}")
    
    # Ensure only doctors can access
    if request.user.role != 'doctor':
        print(f"Non-doctor user {request.user.username} tried to access doctor dashboard")
        return redirect('Home:home')
    
    try:
        # Get the doctor instance associated with the logged-in user
        doctor = Doctor.objects.get(user=request.user)
        print(f"Found doctor profile for {request.user.username}")
        
        # Get all appointments for this doctor
        all_appointments = Appointment.objects.filter(doctor=doctor)
        new_appointments = all_appointments.filter(status='Requested')
        approved_appointments = all_appointments.filter(status='Accepted')
        cancelled_appointments = all_appointments.filter(status='Rejected')
        completed_appointments = all_appointments.filter(payment_status='Completed')
        patient = PatientProfile.objects.get(id=1)  # Or use another query to get the patient
        profile_image = patient.profile_image
        # Get today's appointments
        today = timezone.now().date()
        todays_appointments = all_appointments.filter(
            appointment_date__date=today
        )
        
        # Get upcoming appointments (next 7 days)
        next_week = today + timezone.timedelta(days=7)
        upcoming_appointments = all_appointments.filter(
            appointment_date__date__gt=today,
            appointment_date__date__lte=next_week,
            status='Accepted'
        ).order_by('appointment_date')
        
        # Get unique patient count
        patient_count = all_appointments.values('patient').distinct().count()
        
        # Get recent patients (last 5)
        recent_patients = CustomUser.objects.filter(
            appointment__doctor=doctor,
            role='patient'
        ).distinct().annotate(
            last_visit=Max('appointment__appointment_date')
        ).order_by('-last_visit')[:5]
        
        context = {
            "user": request.user,
            "doctor": doctor,
            "total_appointments": all_appointments.count(),
            "new_appointments": new_appointments.count(),
            "approved_appointments": approved_appointments.count(),
            "cancelled_appointments": cancelled_appointments.count(),
            "completed_appointments": completed_appointments.count(),
            "patient_count": patient_count,
            "todays_appointments": todays_appointments.count(),
            "todays_appointments_list": todays_appointments.order_by('appointment_date'),
            "upcoming_appointments": upcoming_appointments,
            "recent_patients": recent_patients,
            "profile_image": profile_image,
        }
        return render(request, "doctor_dashboard.html", context)
    except Doctor.DoesNotExist:
        print(f"No doctor profile found for user {request.user.username}")
        # Create a basic doctor profile if missing
        if Department.objects.exists():
            doctor = Doctor.objects.create(
                user=request.user,
                doc_name=f"Dr. {request.user.first_name} {request.user.last_name}" if request.user.first_name else request.user.username,
                dep_name=Department.objects.first()
            )
            print(f"Created doctor profile for {request.user.username}")
            return redirect('Home:doctor_dashboard')
        else:
            print("No departments exist to create doctor profile")
            return render(request, "doctor_dashboard.html", {"user": request.user, "error": "No doctor profile found and no departments exist to create one"})

@login_required
def patient_dashboard(request):
    if request.user.role != 'patient':
        return redirect('Home:home')
    
    # Get patient profile
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    # Get patient appointments
    appointments = Appointment.objects.filter(patient=request.user)
    upcoming_appointments = appointments.filter(
        status='Accepted', 
        appointment_date__gte=timezone.now().date()
    ).order_by('appointment_date')[:3]
    
    # Get billing information
    total_paid = Payment.objects.filter(
        user=request.user, 
        stripe_charge_id__isnull=False
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate pending payments from appointments
    pending_payments = appointments.filter(
        payment_status='Pending'
    ).count() * 50.00  # Assuming each appointment costs $50
    
    context = {
        'profile': profile,
        'upcoming_appointments': upcoming_appointments,
        'total_appointments': appointments.count(),
        'completed_appointments': appointments.filter(payment_status='Completed').count(),
        'total_paid': total_paid,
        'pending_payments': pending_payments
    }
    
    return render(request, "patient_dashboard.html", context)

@login_required
def receptionist_MainDashboard(request):
    if request.user.role != 'receptionist':
        return redirect('Home:home')
    
    # Get receptionist profile
    profile, created = ReceptionistProfile.objects.get_or_create(user=request.user)
    
    # Get statistics
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    total_appointments = Appointment.objects.filter(
        created_at__gte=thirty_days_ago
    ).count()
    
    total_patients = Appointment.objects.filter(
        created_at__gte=thirty_days_ago
    ).values('patient').distinct().count()
    
    pending_appointments = Appointment.objects.filter(status='Requested').count()
    
    context = {
        'profile': profile,
        'total_appointments': total_appointments,
        'total_patients': total_patients,
        'pending_appointments': pending_appointments,
    }
    
    return render(request, 'receptionist_MainDashboard.html', context)



# <==============End Login Required For Dashboard======================>

# <==============LogOut======================>
def user_logout(request):
    
    auth_logout(request)
    return redirect('Home:home')

# <==============End LogOut======================>





# <==============Login Required For Role======================>

def index(request):
    return render(request,'index.html')


def about(request):
    # Get doctors and handle those without images
    doctors = []
    for doc in Doctor.objects.all()[:3]:
        # Check if the doctor has an image
        if doc.doc_image and hasattr(doc.doc_image, 'url'):
            doctors.append(doc)
        else:
            # Skip doctors without images for now
            print(f"Doctor {doc.doc_name} has no image, skipping from about page display")
    
    return render(request, 'about.html', {'doctor': doctors})

def doctor(request):
    # Get all doctors and handle those without images
    doctors = []
    for doc in Doctor.objects.all():
        # Check if the doctor has an image
        if doc.doc_image and hasattr(doc.doc_image, 'url'):
            doctors.append(doc)
        else:
            # Skip doctors without images for now
            print(f"Doctor {doc.doc_name} has no image, skipping from display")
    
    return render(request, 'doctor.html', {'doctor': doctors})

def doctor_reg(request):
    
    return render(request,'doctor_reg.html')

def department(request):
    Departments=Department.objects.all()
    return render(request,'department.html',{'Departments':Departments})

def contact(request):
    return render(request,'contact.html')

def logout(request):
    return render(request,'logout.html')

def login(request):
    return render(request,'login.html')

def register(request):
    """
    Main registration page that provides links to specific registration types
    (patient, doctor, receptionist)
    """
    return render(request, 'register.html')

def view_appointments(request):

    return render(request,'view_appointments.html')

# <======Rececptionist appointment==========>
@login_required
def rep_view_appoint(request):
    appointments = Appointment.objects.filter(status='Requested')
    return render(request, 'rep_view_appoint.html', {'appointments': appointments})


@login_required
def doc_view_appoint(request, doctor_id):
    # Get the doctor instance
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Ensure the logged-in user is either the doctor or an admin
    if request.user.role == 'doctor' and doctor.user != request.user:
        print(f"Doctor {request.user.username} tried to access appointments for doctor {doctor.doc_name}")
        return redirect('Home:home')
    
    # Get appointments for this doctor
    appointments = Appointment.objects.filter(doctor=doctor, status='Accepted').order_by('-appointment_date')
    
    context = {
        'doctor': doctor,
        'appointments': appointments
    }
    
    return render(request, 'doc_view_appoint.html', context)


@login_required
def rep_manage_appoint(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            appointment.status = 'Accepted'
            appointment.save()
            print(f"Appointment {appointment_id} accepted by {request.user.username}")
            return redirect('Home:receptionist_dashboard')
        elif action == 'reject':
            appointment.status = 'Rejected'
            appointment.save()
            print(f"Appointment {appointment_id} rejected by {request.user.username}")
            return redirect('Home:receptionist_dashboard')
    
    return render(request, 'rep_manage_appoint.html', {'appointment': appointment})


  # <======End Rececptionist appointment==========>

# <======Doctor appointment==========>



@login_required
def appointment(request):
    appointments = Appointment.objects.filter(patient=request.user)
    
    if request.user.role != CustomUser.PATIENT:
        return redirect('Home:home')  # Redirect non-patient users

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # Create appointment with pending payment status
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.status = 'Pending'  # Set initial status to Pending until payment
            appointment.payment_status = 'Pending'
            appointment.save()
            
            # Redirect to payment page
            return redirect('Home:initiate_payment', appointment_id=appointment.id)
    else:
        form = AppointmentForm()
        # Ensure the doctor queryset is available
        form.fields['doctor'].queryset = Doctor.objects.all().select_related('dep_name')
    
    # Get all departments for the department selection step
    departments = Department.objects.all()
    
    context = {
        'form': form, 
        'appointments': appointments,
        'departments': departments
    }
    return render(request, 'appointment.html', context)


def view_appointment(request):
    appointments = Appointment.objects.filter(patient=request.user)
    
    context={'appointments':appointments}
    
    return render(request,'view_appointments.html',context)


# <==============Dashborads======================>

def receptionist_dashboard(request):
    # Ensure only receptionist can access the dashboard
   
    # Retrieve all appointments with 'Pending' status
    pending_appointments = Appointment.objects.filter(status='Requested')
    
    # Retrieve all appointments with 'Accepted' or 'Rejected' status
    processed_appointments = Appointment.objects.exclude(status='Requested')
    
    context = {
        'pending_appointments': pending_appointments,
        'processed_appointments': processed_appointments,
    }
    
    return render(request, 'receptionist_dashboard.html', context)



# <==============End Dashborads======================>

@login_required
def rep_view_patients(request):
    """
    View for receptionist to see all patients in the database
    """
    # Get all users with patient role
    patients = CustomUser.objects.filter(role='patient')
    
    context = {
        'patients': patients
    }
    
    return render(request, 'rep_view_patients.html', context)
    
@login_required
def rep_view_doctor(request):
    """
    View for receptionist to see all doctors in the database
    """
    # Get all users with patient role
    doctors = CustomUser.objects.filter(role='doctor')
    
    context = {
        'doctors': doctors
    }
    
    return render(request, 'rep_view_doctor.html', context)

# Add these PayPal payment views
@login_required
def initiate_payment(request, appointment_id):
    """
    Initiate a PayPal payment for an appointment
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if the appointment belongs to the logged-in user
    if appointment.patient != request.user:
        return redirect('Home:home')
    
    # Check if payment is already completed
    if appointment.payment_status == 'Completed':
        return redirect('Home:view_appointments')
    
    context = {
        'appointment': appointment,
        'client_id': 'YOUR_PAYPAL_CLIENT_ID',  # Replace with your PayPal client ID
    }
    
    return render(request, 'payment.html', context)

@csrf_exempt
def payment_complete(request):
    """
    Handle PayPal payment completion webhook
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        appointment_id = data.get('appointment_id')
        payment_id = data.get('payment_id')
        
        if appointment_id and payment_id:
            try:
                appointment = Appointment.objects.get(id=appointment_id)
                
                # Update appointment payment status
                appointment.payment_status = 'Completed'
                appointment.payment_id = payment_id
                appointment.status = 'Requested'  # Set status to Requested after payment
                appointment.save()
                
                # Create a Payment record in the database
                Payment.objects.create(
                    user=appointment.patient,
                    amount=Decimal('50.00'),  # Standard appointment fee
                    stripe_charge_id=payment_id,  # Using PayPal payment ID
                )
                
                return JsonResponse({'status': 'success'})
            except Appointment.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Appointment not found'})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def payment_success(request, appointment_id):
    """
    Display payment success page
    """
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if the appointment belongs to the logged-in user
    if appointment.patient != request.user:
        return redirect('Home:home')
    
    return render(request, 'payment_success.html', {'appointment': appointment})

@login_required
def billing_history(request):
    """
    View for displaying patient's billing history
    """
    # Get all appointments for this patient
    appointments = Appointment.objects.filter(patient=request.user)
    
    # Create billing records based on appointments
    billing_records = []
    
    for appointment in appointments:
        # Create a billing record for each appointment
        billing_record = {
            'id': appointment.id,
            'date': appointment.created_at,
            'description': f"Consultation with Dr. {appointment.doctor.doc_name}",
            'amount': 50.00,  # Default consultation fee
            'status': appointment.payment_status,
            'payment_id': appointment.payment_id,
            'appointment': appointment
        }
        billing_records.append(billing_record)
    
    context = {
        'billing_records': billing_records,
        'total_paid': sum(record['amount'] for record in billing_records if record['status'] == 'Completed'),
        'total_pending': sum(record['amount'] for record in billing_records if record['status'] == 'Pending'),
    }
    
    return render(request, 'billing_history.html', context)

@login_required
def profile_settings(request):
    # Ensure only patients can access this view
    if request.user.role != 'patient':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('Home:home')
    
    # Get or create patient profile
    profile, created = PatientProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Handle profile update
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = PatientProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('Home:profile_settings')
        else:
            for form in [user_form, profile_form]:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = PatientProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile
    }
    
    return render(request, 'profile_settings.html', context)

class ReceptionistProfileView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'receptionist_profile.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'receptionistprofile')
    
    def get(self, request):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ReceptionistProfileForm(instance=request.user.receptionistprofile)
        
        # Calculate statistics
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        total_appointments = Appointment.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        total_patients = Appointment.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('patient').distinct().count()
        
        pending_appointments = Appointment.objects.filter(status='Requested').count()
        
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'total_appointments': total_appointments,
            'total_patients': total_patients,
            'pending_appointments': pending_appointments
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ReceptionistProfileForm(
            request.POST,
            request.FILES,
            instance=request.user.receptionistprofile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('Home:receptionist_profile')
        
        context = {
            'user_form': user_form,
            'profile_form': profile_form
        }
        return render(request, self.template_name, context)