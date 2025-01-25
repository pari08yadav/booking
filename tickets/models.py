from django.db import models
from django.contrib.auth.models import AbstractUser 
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
import uuid


# User class for storing user data
class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True) 
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.username
    

# password_reset_token class for reset password when forgot
class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # Define token expiration time (e.g., 1 hour)
        expiration_time = timezone.now() - timedelta(hours=1)  # Use django.utils.timezone.now() here
        return self.created_at < expiration_time


# user balance class for storing user balance in wallet
class UserBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="balance")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Balance: {self.balance}"


# transaction table for storing transction values 
class Transaction(models.Model):
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='transactions', default='')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=now)
    status = models.CharField(max_length=20, choices=[('Success', 'Success'), ('Failed', 'Failed')], default='Success')

    def __str__(self):
        return f"Transaction {self.id} - {self.user.username}"


# Train detail model

class Train(models.Model):
    name = models.CharField(max_length=100)
    train_number = models.CharField(max_length=10, unique=True)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} ({self.train_number})"


# TrainSchedule model for availability on specific dates
class TrainSchedule(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="schedules")
    date = models.DateField()
    available_seats = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.train.name} - {self.date} - Seats: {self.available_seats}"


# Ticket model
class Ticket(models.Model):
    CLASS_CHOICES = [
        ('Sleeper', 'Sleeper'),
        ('First AC', 'First AC'),
        ('Second AC', 'Second AC'),
        ('Third AC', 'Third AC'),
        ('General', 'General'),
    ]
    train_schedule = models.ForeignKey(TrainSchedule,on_delete=models.CASCADE,related_name="tickets",null=True, blank=True)
    seat_number = models.CharField(max_length=10, null=False, blank=False)
    is_booked = models.BooleanField(default=False)
    class_type = models.CharField(max_length=20, choices=CLASS_CHOICES, default='General')


    def __str__(self):
        if self.train_schedule:
            return f"{self.train_schedule.train.name} - {self.seat_number} ({'Booked' if self.is_booked else 'Available'})"
        else:
            return f"Ticket {self.seat_number} - No Train Schedule Assigned"


# Booking model
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    passenger_name = models.CharField(max_length=100, null=False, blank=False, default='')  # Passenger's name
    passenger_age = models.PositiveIntegerField(null=False, blank=False, default=0)  # Passenger's age
    
    def __str__(self):
        return f"Booking {self.id} - {self.user.username} - {self.ticket}"
