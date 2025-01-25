from django.contrib import admin
from .models import User, Transaction

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'ticket', 'total_amount', 'timestamp', 'status')
    list_filter = ('status', 'timestamp')
    search_fields = ('transaction_id', 'user__username', 'ticket__seat_number')
    ordering = ('-timestamp',)
    readonly_fields = ('id', 'timestamp')

    def has_add_permission(self, request):
        """Disallow adding transactions manually via the admin interface."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disallow deleting transactions via the admin interface."""
        return False
