from datetime import timezone
from decimal import Decimal
from django.db import connection
from django.forms import DateField, ValidationError
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from .models import Train, User, UserBalance, Transaction, Ticket, Booking
from .serializers import UserBalanceSerializer, UserSignupSerializer, UserLoginSerializer, ForgotPasswordSerializer, ForgotPasswordConfirmSerializer, TransactionSerializer, TicketSerializer,  BookingSerializer, TrainSchedule
from rest_framework.permissions import IsAuthenticated, IsAdminUser
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


# Search Tickets API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_tickets(request):
    source = request.GET.get('source')
    destination = request.GET.get('destination')
    date = request.GET.get('date')
    
    if not source or not destination:
        return Response(
            {"error": "Both source and destination are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        date_obj = parse_date(date) if date else None
        if date and not date_obj:
            raise ValueError("Invalid date format")
    except ValueError:
        return Response(
            {"error": "Invalid date format. Use YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    # Filter trains by source and destination
    trains = Train.objects.filter(source__icontains=source, destination__icontains=destination)
    if not trains.exists():
        return Response(
            {"message": "No trains found for the given source and destination."},
            status=status.HTTP_200_OK
        )

    schedules = TrainSchedule.objects.filter(train__in=trains)
    if date_obj:
        schedules = schedules.filter(date=date_obj)

    if not schedules.exists():
        return Response(
            {"message": "No schedules available for the given criteria."},
            status=status.HTTP_200_OK
        )
    
    # Custom response format
    response_data = []
    for schedule in schedules:
        train = schedule.train
        response_data.append({
            "train_name": train.name,
            "date": schedule.date,
            "available_seats": schedule.available_seats,
            "train_schedule_id": schedule.id,  # Include the train schedule ID
            "source": train.source,
            "destination": train.destination,
        })

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_ticket(request):
    passengers = request.data.get('passengers', [])  # List of passenger details
    train_schedule_id = request.data.get('train_schedule_id')  # Train schedule ID
    payment_status = request.data.get('payment_status', 'Pending')

    # Validate input
    if not passengers or not isinstance(passengers, list):
        return Response({"error": "Passenger details are required and must be a list."}, status=status.HTTP_400_BAD_REQUEST)

    if not train_schedule_id:
        return Response({"error": "Train schedule ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    valid_payment_statuses = ['Pending', 'Completed', 'Failed']
    if payment_status not in valid_payment_statuses:
        return Response({"error": "Invalid payment status."}, status=status.HTTP_400_BAD_REQUEST)

    # Fetch the train schedule
    try:
        train_schedule = TrainSchedule.objects.get(id=train_schedule_id)
    except TrainSchedule.DoesNotExist:
        return Response({"error": "Train schedule not found."}, status=status.HTTP_404_NOT_FOUND)

    if train_schedule.available_seats < len(passengers):
        return Response({"error": "Not enough seats available."}, status=status.HTTP_400_BAD_REQUEST)

    # Calculate the total fare
    ticket_price = train_schedule.train.price
    total_fare = ticket_price * len(passengers) 
    
    # Check user balance
    user_balance = UserBalance.objects.get(user=request.user)
    if user_balance.balance < total_fare:
        return Response({"error": "Insufficient balance to book tickets."}, status=status.HTTP_400_BAD_REQUEST)

    
    bookings = []  # To store booking details for response
    cursor = connection.cursor()
    
    try:
        # Begin a manual database transaction
        cursor.execute("BEGIN")
        
        for passenger in passengers:
            # Validate passenger details
            passenger_name = passenger.get('name')
            passenger_age = passenger.get('age')
            class_type = passenger.get('classType')

            if not passenger_name or not passenger_age or not class_type:
                return Response({"error": "Valid passenger name, age, and class type are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Generate a unique seat number (e.g., based on available seats)
            seat_number = f"SN-{train_schedule.id}-{train_schedule.available_seats}"

            # Create and book the ticket
            ticket = Ticket.objects.create(
                train_schedule=train_schedule,
                seat_number=seat_number,
                is_booked=True,
                class_type=class_type
            )

            # Reduce available seats in the train schedule
            train_schedule.available_seats -= 1
            train_schedule.save()

            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                ticket=ticket,
                passenger_name=passenger_name,
                passenger_age=passenger_age,
                payment_status=payment_status
            )
            # Append booking details to the bookings list
            bookings.append({
                "booking_id": booking.id,
                "ticket_id": ticket.id,
                "seat_number": ticket.seat_number,
                "passenger_name": passenger_name.capitalize(),
                "passenger_age": passenger_age,
                "class_type": class_type,
                "fare": ticket_price,
                "train_name": train_schedule.train.name.capitalize(),
                "train_number": train_schedule.train.train_number,
                "source": train_schedule.train.source.capitalize(),
                "destination": train_schedule.train.destination.capitalize(),
                "date": train_schedule.date,
            })
            
        # Deduct the fare from the user's balance
        user_balance.balance -= total_fare
        user_balance.save()
        
        # Create a single transaction entry for the entire booking
        Transaction.objects.create(
            user=request.user,
            ticket = ticket,
            total_amount=total_fare,
            # timestamp=timezone.now(),
            status='Success'
        )
        
        # Commit the transaction
        cursor.execute("COMMIT")
        return Response(
            {"message": "Tickets booked successfully!", "bookings": bookings},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error: {e}")
        return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# View Bookings API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('ticket__train_schedule')
    serializer = BookingSerializer(bookings, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Cancel Booking API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_booking(request):
    booking_id = request.data.get('booking_id')

    if not booking_id:
        return Response({"error": "Booking ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        booking = Booking.objects.select_related('ticket__train_schedule').get(id=booking_id, user=request.user)
        ticket = booking.ticket
        train_schedule = ticket.train_schedule

        # Mark ticket as not booked
        ticket.is_booked = False
        ticket.save()

        # Increment available seats in the train schedule
        if train_schedule:
            train_schedule.available_seats += 1
            train_schedule.save()

        # Delete the booking
        booking.delete()

        return Response({"message": "Booking canceled successfully."}, status=status.HTTP_200_OK)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)


# Add fund in waller view
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_fund(request):
    user = request.user
    amount = request.data.get('amount')
    
    # Validate the amount
    if not amount:
        return Response({"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount = Decimal(amount)  # Convert to Decimal
        if amount <= 0:
            return Response({"error": "Amount must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)
    except:
        return Response({"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)
    
    user_balance, created = UserBalance.objects.get_or_create(user=user)
    user_balance.balance += amount
    user_balance.save()
    
    # Serialize the updated balance
    serializer = UserBalanceSerializer(user_balance)
    return Response({"message": "Amount added successfully", "data":serializer.data}, status=200)



# Check balance api view
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_balance(request):
    user_balance, created = UserBalance.objects.get_or_create(user=request.user)
    serializer = UserBalanceSerializer(user_balance)
    return Response(serializer.data, status=status.HTTP_200_OK)


# Admin view balances all user
# @api_view(['GET'])
# @permission_classes([IsAdminUser])
# def admin_view_balances(request):
#     balances = UserBalance.objects.all()
#     serializer = UserBalanceSerializer(balances, many=True)
#     return Response(serializer.data, status=status.HTTP_200_OK)
