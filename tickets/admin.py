from django.contrib import admin
from .models import User, Transaction

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')



@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount', 'type', 'timestamp')  # Use 'timestamp' instead of 'created_at'
    search_fields = ('user__username', 'amount')
    list_filter = ('type', 'timestamp')  # Use 'timestamp' instead of 'created_at'
