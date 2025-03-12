from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from . models import *
import csv
from django.http import HttpResponse
from decimal import Decimal

# Register your models here.

class CustomAdminSite(admin.AdminSite):
    site_header = 'Hospital Management System'
    site_title = 'HMS Admin Portal'
    index_title = 'Hospital Administration'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        # Redirect the admin index to our custom dashboard
        return self.dashboard_view(request)
    
    def dashboard_view(self, request):
        # Get statistics for the dashboard
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        # User statistics
        total_users = CustomUser.objects.count()
        total_patients = CustomUser.objects.filter(role='patient').count()
        total_doctors = CustomUser.objects.filter(role='doctor').count()
        total_receptionists = CustomUser.objects.filter(role='receptionist').count()
        
        # Appointment statistics
        total_appointments = Appointment.objects.count()
        pending_appointments = Appointment.objects.filter(status='Requested').count()
        completed_appointments = Appointment.objects.filter(status='Accepted', payment_status='Completed').count()
        rejected_appointments = Appointment.objects.filter(status='Rejected').count()
        
        # Department statistics
        departments = Department.objects.annotate(
            doctor_count=Count('doctor', distinct=True),
            appointment_count=Count('doctor__appointment', distinct=True)
        ).order_by('-appointment_count')[:5]
        
        # Recent appointments
        recent_appointments = Appointment.objects.select_related(
            'patient', 'doctor', 'doctor__dep_name'
        ).order_by('-created_at')[:10]
        
        # Payment statistics
        total_revenue = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        recent_payments = Payment.objects.select_related('user').order_by('-timestamp')[:5]
        
        # Monthly appointment data for chart
        last_six_months = []
        for i in range(5, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            month_name = month_start.strftime('%b')
            count = Appointment.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            last_six_months.append({'month': month_name, 'count': count})
        
        # Department distribution for pie chart
        department_stats = Department.objects.annotate(
            appointment_count=Count('doctor__appointment', distinct=True)
        ).values('dep_name', 'appointment_count')
        
        context = {
            'title': 'Hospital Dashboard',
            'total_users': total_users,
            'total_patients': total_patients,
            'total_doctors': total_doctors,
            'total_receptionists': total_receptionists,
            'total_appointments': total_appointments,
            'pending_appointments': pending_appointments,
            'completed_appointments': completed_appointments,
            'rejected_appointments': rejected_appointments,
            'departments': departments,
            'recent_appointments': recent_appointments,
            'total_revenue': total_revenue,
            'recent_payments': recent_payments,
            'last_six_months': last_six_months,
            'department_stats': department_stats,
            'has_permission': True,
            'site_url': '/',
            'site_title': self.site_title,
            'site_header': self.site_header,
            'available_apps': self.get_app_list(request),
        }
        
        return TemplateResponse(request, 'admin/dashboard.html', context)
    
admin_site = CustomAdminSite(name='hospital_admin')

# Custom User Admin
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'date_joined', 'is_active')
    list_display_links = ('username', 'email')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 20
    show_full_result_count = True
    
    fieldsets = (
        ('Account Information', {
            'fields': ('username', 'email', 'password'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'role'),
            'classes': ('wide',),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            appointment_count=Count('appointment', distinct=True),
        )
        return queryset

# Department Admin
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('dep_name', 'doctor_count', 'appointment_count', 'created_at', 'display_image')
    list_display_links = ('dep_name', 'display_image')
    search_fields = ('dep_name',)
    list_filter = ('created_at',)
    list_per_page = 15
    readonly_fields = ('created_at', 'doctor_count', 'appointment_count')
    
    fieldsets = (
        ('Department Information', {
            'fields': ('dep_name', 'dep_description', 'dep_image'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Statistics', {
            'fields': ('doctor_count', 'appointment_count', 'created_at'),
            'classes': ('collapse',),
        }),
    )
    
    def doctor_count(self, obj):
        count = obj.doctor.count()
        return format_html('<span class="badge badge-primary">{}</span>', count)
    doctor_count.short_description = 'Doctors'
    
    def appointment_count(self, obj):
        count = Appointment.objects.filter(doctor__dep_name=obj).count()
        return format_html('<span class="badge badge-success">{}</span>', count)
    appointment_count.short_description = 'Appointments'
    
    def display_image(self, obj):
        if obj.dep_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.dep_image.url)
        return "No Image"
    display_image.short_description = 'Image'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            doctor_count=Count('doctor', distinct=True),
        )
        return queryset

# Doctor Admin
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('doc_name', 'department', 'appointment_count', 'display_image', 'user_link')
    list_display_links = ('doc_name', 'display_image')
    list_filter = ('dep_name', 'created_at')
    search_fields = ('doc_name', 'dep_name__dep_name')
    list_per_page = 15
    autocomplete_fields = ['dep_name', 'user']
    
    fieldsets = (
        ('Doctor Information', {
            'fields': ('doc_name', 'dep_name', 'doc_image', 'user'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'appointment_count')
    
    def department(self, obj):
        if obj.dep_name:
            return format_html('<span class="badge" style="background-color: #4e73df;">{}</span>', obj.dep_name.dep_name)
        return "No Department"
    department.short_description = 'Department'
    
    def appointment_count(self, obj):
        count = Appointment.objects.filter(doctor=obj).count()
        return format_html('<span class="badge badge-success">{}</span>', count)
    appointment_count.short_description = 'Appointments'
    
    def display_image(self, obj):
        if obj.doc_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.doc_image.url)
        return "No Image"
    display_image.short_description = 'Image'
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:Home_customuser_change', args=[obj.user.id])
            return format_html('<a href="{}" class="btn btn-sm btn-info">{}</a>', url, obj.user.username)
        return "No User"
    user_link.short_description = 'User Account'

# Appointment Admin
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_name', 'doctor_name', 'department', 'appointment_date', 'status_badge', 'payment_status_badge', 'actions_buttons')
    list_display_links = ('id', 'patient_name')
    list_filter = ('status', 'payment_status', 'appointment_date', 'doctor__dep_name')
    search_fields = ('patient__username', 'doctor__doc_name', 'reason')
    date_hierarchy = 'appointment_date'
    list_per_page = 20
    autocomplete_fields = ['patient', 'doctor']
    actions = ['mark_as_accepted', 'mark_as_rejected', 'mark_payment_completed']
    
    fieldsets = (
        ('Appointment Information', {
            'fields': ('patient', 'doctor', 'appointment_date', 'reason'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Status Information', {
            'fields': ('status', 'payment_status', 'payment_id'),
            'classes': ('wide',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def patient_name(self, obj):
        name = f"{obj.patient.first_name} {obj.patient.last_name}" if obj.patient.first_name else obj.patient.username
        return format_html('<strong>{}</strong>', name)
    patient_name.short_description = 'Patient'
    
    def doctor_name(self, obj):
        return obj.doctor.doc_name
    doctor_name.short_description = 'Doctor'
    
    def department(self, obj):
        if obj.doctor.dep_name:
            return format_html('<span class="badge" style="background-color: #4e73df;">{}</span>', obj.doctor.dep_name.dep_name)
        return "No Department"
    department.short_description = 'Department'
    
    def status_badge(self, obj):
        colors = {
            'Requested': 'warning',
            'Accepted': 'success',
            'Rejected': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge badge-{}">{}</span>', color, obj.status)
    status_badge.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        colors = {
            'Pending': 'warning',
            'Completed': 'success',
            'Failed': 'danger',
        }
        color = colors.get(obj.payment_status, 'secondary')
        return format_html('<span class="badge badge-{}">{}</span>', color, obj.payment_status)
    payment_status_badge.short_description = 'Payment'
    
    def actions_buttons(self, obj):
        buttons = ""
        if obj.status != 'Accepted':
            buttons += format_html('<a href="{}?id={}" class="btn btn-xs btn-success mr-1">Accept</a>', 
                                  reverse('admin:accept_appointment'), obj.id)
        if obj.status != 'Rejected':
            buttons += format_html('<a href="{}?id={}" class="btn btn-xs btn-danger mr-1">Reject</a>', 
                                  reverse('admin:reject_appointment'), obj.id)
        if obj.payment_status != 'Completed':
            buttons += format_html('<a href="{}?id={}" class="btn btn-xs btn-primary">Complete Payment</a>', 
                                  reverse('admin:complete_payment'), obj.id)
        return buttons
    actions_buttons.short_description = 'Actions'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('accept-appointment/', self.admin_site.admin_view(self.accept_appointment), name='accept_appointment'),
            path('reject-appointment/', self.admin_site.admin_view(self.reject_appointment), name='reject_appointment'),
            path('complete-payment/', self.admin_site.admin_view(self.complete_payment), name='complete_payment'),
        ]
        return custom_urls + urls
    
    def accept_appointment(self, request):
        appointment_id = request.GET.get('id')
        if appointment_id:
            appointment = Appointment.objects.get(id=appointment_id)
            appointment.status = 'Accepted'
            appointment.save()
            self.message_user(request, f"Appointment #{appointment_id} has been accepted")
        return redirect(reverse('admin:Home_appointment_changelist'))
    
    def reject_appointment(self, request):
        appointment_id = request.GET.get('id')
        if appointment_id:
            appointment = Appointment.objects.get(id=appointment_id)
            appointment.status = 'Rejected'
            appointment.save()
            self.message_user(request, f"Appointment #{appointment_id} has been rejected")
        return redirect(reverse('admin:Home_appointment_changelist'))
    
    def complete_payment(self, request):
        appointment_id = request.GET.get('id')
        if appointment_id:
            appointment = Appointment.objects.get(id=appointment_id)
            appointment.payment_status = 'Completed'
            appointment.save()
            
            # Create a Payment record
            Payment.objects.create(
                user=appointment.patient,
                amount=Decimal('50.00'),  # Standard appointment fee
                stripe_charge_id=f"admin_payment_{appointment.id}_{int(timezone.now().timestamp())}",
            )
            
            self.message_user(request, f"Payment for appointment #{appointment_id} has been marked as completed")
        return redirect(reverse('admin:Home_appointment_changelist'))
    
    def mark_as_accepted(self, request, queryset):
        queryset.update(status='Accepted')
        self.message_user(request, f"{queryset.count()} appointments have been accepted")
    mark_as_accepted.short_description = "Mark selected appointments as accepted"
    
    def mark_as_rejected(self, request, queryset):
        queryset.update(status='Rejected')
        self.message_user(request, f"{queryset.count()} appointments have been rejected")
    mark_as_rejected.short_description = "Mark selected appointments as rejected"
    
    def mark_payment_completed(self, request, queryset):
        from decimal import Decimal
        payment_count = 0
        
        for appointment in queryset:
            appointment.payment_status = 'Completed'
            appointment.save()
            
            # Create a Payment record for each appointment
            Payment.objects.create(
                user=appointment.patient,
                amount=Decimal('50.00'),  # Standard appointment fee
                stripe_charge_id=f"admin_bulk_payment_{appointment.id}_{int(timezone.now().timestamp())}",
            )
            payment_count += 1
        
        self.message_user(request, f"Payment for {payment_count} appointments has been marked as completed")
    mark_payment_completed.short_description = "Mark selected appointments as payment completed"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('patient', 'doctor', 'doctor__dep_name')
        return queryset

# Payment Admin
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_name', 'amount_display', 'payment_date', 'stripe_charge_id', 'related_appointment', 'payment_status')
    list_display_links = ('id', 'user_name')
    list_filter = ('timestamp', 'amount')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'stripe_charge_id')
    date_hierarchy = 'timestamp'
    list_per_page = 20
    actions = ['export_as_csv']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('user', 'amount', 'stripe_charge_id'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('timestamp',)
    
    def user_name(self, obj):
        name = f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name else obj.user.username
        return format_html('<strong>{}</strong>', name)
    user_name.short_description = 'User'
    
    def amount_display(self, obj):
        return format_html('<span class="badge badge-success" style="font-size: 14px; padding: 8px 12px;">${}</span>', obj.amount)
    amount_display.short_description = 'Amount'
    
    def payment_date(self, obj):
        return format_html('<span style="color: #666;">{}</span>', obj.timestamp.strftime("%b %d, %Y"))
    payment_date.short_description = 'Payment Date'
    
    def related_appointment(self, obj):
        # Find appointments related to this payment
        appointments = Appointment.objects.filter(payment_id=obj.stripe_charge_id)
        if appointments.exists():
            appointment = appointments.first()
            return format_html(
                '<a href="{}" class="btn btn-info btn-sm">'
                '<i class="fas fa-calendar-check"></i> Appointment #{}</a>',
                reverse('admin:Home_appointment_change', args=[appointment.id]),
                appointment.id
            )
        return format_html('<span class="badge badge-secondary">No appointment</span>')
    related_appointment.short_description = 'Related Appointment'
    
    def payment_status(self, obj):
        # Check if this payment is linked to any appointment
        appointments = Appointment.objects.filter(payment_id=obj.stripe_charge_id)
        if appointments.exists():
            status = appointments.first().payment_status
            if status == 'Completed':
                return format_html('<span class="badge badge-success">Completed</span>')
            elif status == 'Failed':
                return format_html('<span class="badge badge-danger">Failed</span>')
            else:
                return format_html('<span class="badge badge-warning">Pending</span>')
        return format_html('<span class="badge badge-info">Standalone</span>')
    payment_status.short_description = 'Status'
    
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta}-{timezone.now().strftime("%Y-%m-%d")}.csv'
        writer = csv.writer(response)
        
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        
        self.message_user(request, f"Successfully exported {queryset.count()} payments")
        return response
    export_as_csv.short_description = "Export selected payments as CSV"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user')
        return queryset

# Patient Profile Admin
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'phone_number', 'blood_group', 'appointment_count', 'display_image')
    list_display_links = ('patient_name', 'display_image')
    list_filter = ('blood_group', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')
    list_per_page = 15
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'profile_image'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Personal Information', {
            'fields': ('phone_number', 'address', 'date_of_birth', 'blood_group'),
            'classes': ('wide',),
        }),
        ('Medical Information', {
            'fields': ('allergies', 'medical_conditions'),
            'classes': ('wide',),
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_number'),
            'classes': ('wide',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def patient_name(self, obj):
        name = f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name else obj.user.username
        return format_html('<strong>{}</strong>', name)
    patient_name.short_description = 'Patient'
    
    def appointment_count(self, obj):
        count = Appointment.objects.filter(patient=obj.user).count()
        return format_html('<span class="badge badge-primary">{}</span>', count)
    appointment_count.short_description = 'Appointments'
    
    def display_image(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.profile_image.url)
        return "No Image"
    display_image.short_description = 'Image'

# Receptionist Profile Admin
class ReceptionistProfileAdmin(admin.ModelAdmin):
    list_display = ('receptionist_name', 'phone_number', 'shift_badge', 'display_image')
    list_display_links = ('receptionist_name', 'display_image')
    list_filter = ('shift', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')
    list_per_page = 15
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'profile_image'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Personal Information', {
            'fields': ('phone_number', 'address', 'date_of_birth', 'shift'),
            'classes': ('wide',),
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_number'),
            'classes': ('wide',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def receptionist_name(self, obj):
        name = f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name else obj.user.username
        return format_html('<strong>{}</strong>', name)
    receptionist_name.short_description = 'Receptionist'
    
    def shift_badge(self, obj):
        colors = {
            'morning': 'success',
            'afternoon': 'warning',
            'night': 'primary',
        }
        color = colors.get(obj.shift, 'secondary')
        return format_html('<span class="badge badge-{}">{}</span>', color, obj.get_shift_display())
    shift_badge.short_description = 'Shift'
    
    def display_image(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.profile_image.url)
        return "No Image"
    display_image.short_description = 'Image'

# Register models with custom admin classes
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(PatientProfile, PatientProfileAdmin)
admin.site.register(ReceptionistProfile, ReceptionistProfileAdmin)

# Register models with custom admin site
admin_site.register(CustomUser, CustomUserAdmin)
admin_site.register(Department, DepartmentAdmin)
admin_site.register(Doctor, DoctorAdmin)
admin_site.register(Appointment, AppointmentAdmin)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(PatientProfile, PatientProfileAdmin)
admin_site.register(ReceptionistProfile, ReceptionistProfileAdmin)