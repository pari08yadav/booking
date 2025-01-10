from django.contrib import admin
from django.urls import path
from .views import signup, login, forgot_password_request
from tickets import views

urlpatterns = [
    path('api/signup/', signup, name='signup'),
    path('api/login/', login, name="login"),
    path('api/forgot/paasword/request/', forgot_password_request, name="forgot_password_request" ),
    path('api/password/forgot/confirm/', views.forgot_password_confirm, name="forgot_password_confrim"),
    path('api/transaction/', views.create_transaction, name="create_transaction"),
    path('api/search/tickets/', views.search_tickets, name="search_tickets"),
    path('api/book/ticket/', views.book_ticket, name="book_ticket"),
    path('api/view/booking/', views.view_bookings, name="view_booking"),
    path('api/cancel/booking/', views.cancel_booking, name="cancel_booking"),
    path('api/add/fund/', views.add_fund, name="add_fund"),
    path('api/check/balance/', views.check_balance, name="check_balance"),
]
