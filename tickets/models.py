from django.db import models
from django.contrib.auth.models import AbstractUser 
from datetime import timedelta
from django.utils import timezone
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
    CREDIT = 'credit'
    DEBIT = 'debit'
    
    TRANSACTION_TYPES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]

    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_transactions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=6, choices=TRANSACTION_TYPES)
    product_id = models.CharField(max_length=255, null=True, blank=True)  # Optional for specific products
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} ({self.type}): {self.amount}"


# Train detail model
from django.db import models

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


# Ticket model
class Ticket(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name="tickets")
    date = models.DateField()
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"Ticket for {self.train.name} on {self.date}"


