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
]
