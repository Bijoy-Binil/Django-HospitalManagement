# Generated by Django 5.1.5 on 2025-02-03 20:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0007_appointment_status_doctor_user_alter_doctor_dep_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appointment',
            old_name='doctor_name',
            new_name='doctor',
        ),
    ]
