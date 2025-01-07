from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from .models import User, UserBalance, Transaction, Ticket
from .serializers import UserSignupSerializer, UserLoginSerializer, ForgotPasswordSerializer, ForgotPasswordConfirmSerializer, TransactionSerializer, TicketSerializer, TrainSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date



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
        # Generate JWT token
        tokens = serializer.create_jwt_token(user)
        
        return Response(
            {
                "message": "Login successful",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "phone_number": user.phone_number,
                },
                "tokens": tokens  # Include the tokens in the response
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



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_transaction(request):
    user = request.user  # Assuming authentication is in place
    data = request.data
    
    # Validate transaction type
    transaction_type = data.get('type')
    if transaction_type not in ['CREDIT', 'DEBIT']:
        return Response({"error": "Invalid transaction type."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch user's balance
    user_balance, created = UserBalance.objects.get_or_create(user=user)

    # Perform balance updates
    from decimal import Decimal
    amount = Decimal(data.get('amount', '0'))
    if transaction_type == 'DEBIT' and user_balance.balance < amount:
        return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

    # Update balance
    if transaction_type == 'DEBIT':
        user_balance.balance -= amount
    elif transaction_type == 'CREDIT':
        user_balance.balance += amount
    user_balance.save()

    # Create the transaction
    transaction = Transaction.objects.create(
        user=user,
        admin=data.get('admin'),  # Assuming admin ID is passed
        amount=amount,
        type=transaction_type,
        product_id=data.get('product_id', None)
    )

    serializer = TransactionSerializer(transaction)
    return Response(serializer.data, status=status.HTTP_201_CREATED)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_tickets(request):
    source = request.GET.get('source')
    destination = request.GET.get('destination')
    date = request.GET.get('date')

    if not (source and destination):
        return Response(
            {"error": "Source and destination are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        if date:
            date_obj = parse_date(date)
            if not date_obj:
                raise ValueError
        else:
            date_obj = None
    except ValueError:
        return Response(
            {"error": "Invalid date format. Use YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Filter tickets
    if date_obj:
        tickets = Ticket.objects.filter(
            train__source__iexact=source,
            train__destination__iexact=destination,
            date=date_obj,
            is_booked=False
        )
    else:
        tickets = Ticket.objects.filter(
            train__source__iexact=source,
            train__destination__iexact=destination,
            is_booked=False
        )
        
    if not tickets.exists():
        return Response(
            {"message": "No tickets available for the given criteria."},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = TicketSerializer(tickets, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)