from rest_framework import serializers
from .models import User, PasswordResetToken
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
import secrets

class UserSignupSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only':True},
        }
        
    def validate_username(self,value):
        if not (4 < len(value) < 20):
            raise serializers.ValidationError(
                "Username must be greater than 4 and smaller than 20 characters."
            )
        return value
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'password':"Password do not match."})
        return data
    
    def create(self, validated_data):
        # Remove confirm_password as it's not part of the model
        validated_data.pop('confirm_password')
        
        # Hash the password before saving the user
        validated_data['password'] = make_password(validated_data['password'])
        
        return super().create(validated_data)
    
    

class UserLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        identifier = data.get('identifier')
        password = data.get('password')
        
        # Try to find the user by email
        user = User.objects.get(email = identifier)
        if not user:
            # If not found by email, try phone number
            user = User.objects.filter(phone_number=identifier).first()
            
        if not user:
            raise serializers.ValidationError("Invalid email/phone number or password.")
        
        # Check if the password is correct
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email/phone number or password.")
        
        # Add the user object to the validated data
        data['user'] = user
        return data
    
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        # Check if a user with this email exists
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    
    def create_reset_token(self, user):
        # Generate a secure token
        token = secrets.token_urlsafe(25)
        
        # Store the token in the PasswordResetToken model
        PasswordResetToken.objects.create(user=user, token=token)
        return token
    
    def send_reset_email(self, email, token):
        # Construct the reset link
        reset_link = f'https://yourdomain.com/reset-password?token={token}'
        
        # Send the reset email
        send_mail(
            subject="Password Reset Request",
            message=f"Click the link below to reset your password:\n{reset_link}",
            from_email="yadav.parishram@gmail.com",
            recipient_list=[email],
        )

    def save(self):
        # Get the validated email
        email = self.validated_data['email']
        
        # Retrieve the user associated with the email
        user = User.objects.get(email=email)
        
        # Create a reset token
        token = self.create_reset_token(user)
        
        # Send the reset email
        self.send_reset_email(email, token)
        
        
        
class ForgotPasswordConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        # Check if passwords match
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def validate_token(self, value):
        # Check if the token is valid
        try:
            # Check if the token exists and is valid
            token_obj = PasswordResetToken.objects.get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")
        
        # Check if the token is expired (if you have expiration logic)
        if token_obj.is_expired():
            raise serializers.ValidationError("Token has expired.")
        
        return value

    def save(self):
        # Retrieve the token and user
        token = self.validated_data['token']
        token_obj = PasswordResetToken.objects.get(token=token)
        user = token_obj.user
        
        # Set the new password for the user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        
        # Optionally, delete the token after use
        token_obj.delete()
        
        return user