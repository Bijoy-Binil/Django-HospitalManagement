"""
URL configuration for Hospital project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
app_name='Home'

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.index,name='home' ),
    path('about',views.about,name='about' ),
    path('doctor',views.doctor,name='doctor' ),
    path('department',views.department,name='department' ),
    path('contact',views.contact,name='contact' ),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('appointment',views.appointment,name='appointment' ),
    path('view_appointments',views.view_appointment,name='view_appointments' ),
    
    # Main registration page
    path('register/', views.register, name='register'),
    
    # Dashboard URLs
    path("patient-dashboard/", views.patient_dashboard, name="patient_dashboard"),
    path("doctor-dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("receptionist-dashboard/", views.receptionist_dashboard, name="receptionist_dashboard"),
    path('receptionist_MainDashboard', views.receptionist_MainDashboard, name='receptionist_MainDashboard'),
    
    # Registration URLs
    path('register/doctor/', views.register_doctor, name='register_doctor'),
    path('register/patient/', views.register_patient, name='register_patient'),
    path('register/receptionist/', views.register_receptionist, name='register_receptionist'),
    
    # Appointment management URLs
    path('rep_manage_appoint/<int:appointment_id>/', views.rep_manage_appoint, name='rep_manage_appoint'),
    path('rep_view_appoint', views.rep_view_appoint, name='rep_view_appoint'),
    path('rep_view_patients', views.rep_view_patients, name='rep_view_patients'),
    path('rep_view_doctor', views.rep_view_doctor, name='rep_view_doctor'),
    path('doc_view_appoint/<int:doctor_id>/', views.doc_view_appoint, name='doc_view_appoint'),
    
    # Payment URLs
    path('payment/<int:appointment_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/complete/', views.payment_complete, name='payment_complete'),
    path('payment/success/<int:appointment_id>/', views.payment_success, name='payment_success'),
    path('billing/history/', views.billing_history, name='billing_history'),
    
    # Profile settings
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('receptionist/profile/', views.ReceptionistProfileView.as_view(), name='receptionist_profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
