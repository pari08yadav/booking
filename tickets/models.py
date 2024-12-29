from django.db import models
from django.contrib.auth.models import AbstractUser 
from datetime import timedelta
from django.utils import timezone

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True) 
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.username
    

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # Define token expiration time (e.g., 1 hour)
        expiration_time = timezone.now() - timedelta(hours=1)  # Use django.utils.timezone.now() here
        return self.created_at < expiration_time