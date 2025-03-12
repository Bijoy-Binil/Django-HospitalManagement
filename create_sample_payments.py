import os
import django
import random
from decimal import Decimal
from datetime import timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hospital.settings')
django.setup()

# Import models after Django setup
from Home.models import Payment, CustomUser, Appointment
from django.utils import timezone

def create_sample_payments():
    # Get all users
    users = CustomUser.objects.all()
    
    if not users.exists():
        print("No users found in the database. Please create users first.")
        return
    
    # Get all appointments
    appointments = Appointment.objects.all()
    
    # Create sample payments
    payment_count = 0
    
    # Create payments linked to appointments
    for appointment in appointments:
        # Only create payments for some appointments to maintain data integrity
        if random.choice([True, False]):
            amount = Decimal(random.choice(['50.00', '75.00', '100.00', '150.00', '200.00']))
            stripe_id = f"stripe_charge_{appointment.id}_{int(timezone.now().timestamp())}"
            
            payment = Payment.objects.create(
                user=appointment.patient,
                amount=amount,
                stripe_charge_id=stripe_id,
                timestamp=appointment.created_at + timedelta(hours=random.randint(1, 24))
            )
            
            # Update appointment payment status and payment_id
            appointment.payment_status = 'Completed'
            appointment.payment_id = stripe_id
            appointment.save()
            
            payment_count += 1
    
    # Create some standalone payments (not linked to appointments)
    for _ in range(5):
        user = random.choice(users)
        amount = Decimal(random.choice(['25.00', '35.00', '45.00', '55.00', '65.00']))
        stripe_id = f"stripe_standalone_{int(timezone.now().timestamp())}_{random.randint(1000, 9999)}"
        
        Payment.objects.create(
            user=user,
            amount=amount,
            stripe_charge_id=stripe_id,
            timestamp=timezone.now() - timedelta(days=random.randint(1, 30))
        )
        
        payment_count += 1
    
    print(f"Successfully created {payment_count} sample payments.")

if __name__ == "__main__":
    create_sample_payments() 