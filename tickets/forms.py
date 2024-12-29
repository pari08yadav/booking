from django import forms
from .models import User

class UserSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password', 'confirm_password']
        
        
    def clean_phone_number( self):
        phone_number = self.cleaned_data.get('phone_number')
        
        if not phone_number:
            raise forms.ValidationError("Phone number is required.")
        
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone Number must contain only digits.")
        
        if len(phone_number) < 10 or len(phone_number) > 15:
            raise forms.ValidationError("Phone number must be between 10 nd 15 digits.")
        
        return phone_number
    
        
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        if password != confirm_password:
            raise forms.ValidationError("Password do not match.")
        
        return cleaned_data
    