from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import User
from .serializers import UserSignupSerializer, UserLoginSerializer, ForgotPasswordSerializer, ForgotPasswordConfirmSerializer
import secrets

@api_view(['POST'])
def signup(request):
    data = request.data
    serializer = UserSignupSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {'message': "User created successfully.", "user":serializer.data},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    data = request.data
    serializer = UserLoginSerializer(data=data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        return Response(
            {
                "message":"Login successful",
                "user":{
                    "username": user.username,
                    "email": user.email,
                    "phone_number": user.phone_number,
                }
            },
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['POST'])
def forgot_password_request(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():   
        serializer.save()
        return Response(
                {"message": "Password reset email has been sent successfully."},
                status=status.HTTP_200_OK
            )
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def forgot_password_confirm(request):
    # Initialize the serializer with the request data
    serializer = ForgotPasswordConfirmSerializer(data=request.data)
    
    # Validate the data
    if serializer.is_valid():
        # Save the new password (this will update the user's password)
        serializer.save()
        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
    
    # Return validation errors if the data is not valid
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
