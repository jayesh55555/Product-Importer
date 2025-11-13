from django.contrib import admin
from .models import Product, Webhook


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'active', 'created_at', 'updated_at')
    list_filter = ('active', 'created_at', 'updated_at')
    search_fields = ('sku', 'name', 'description')
    list_editable = ('active',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('sku', 'name', 'description', 'active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_url', 'event_type', 'is_active', 'created_at')
    list_filter = ('event_type', 'is_active', 'created_at')
    search_fields = ('name', 'target_url')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')