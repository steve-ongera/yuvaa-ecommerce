from django.contrib import admin
from .models import Order , OrderDetail , Cart , CartDetail ,Coupon ,Transaction

class OrderAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'status', 'total_price', 'pickup_station', 'order_time')
    search_fields = ('code', 'user__username', 'status')
    list_filter = ('status', 'pickup_station')
    ordering = ('-order_time',)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'order', 'amount', 'status', 'timestamp')
    search_fields = ('transaction_id', 'user__username', 'order__code')
    list_filter = ('status',)
    ordering = ('-timestamp',)


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Order, OrderAdmin)

admin.site.register(OrderDetail)
admin.site.register(Cart)
admin.site.register(CartDetail)
admin.site.register(Coupon)