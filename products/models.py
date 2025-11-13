from django.db import models


class Product(models.Model):
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Ensure case-insensitive uniqueness for SKU
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower('sku'),
                name='unique_lower_sku'
            )
        ]
    
    def save(self, *args, **kwargs):
        # Convert SKU to uppercase for consistency
        self.sku = self.sku.upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.sku} - {self.name}"



class Webhook(models.Model):
    EVENT_CHOICES = [
        ('product.created', 'Product Created'),
        ('product.updated', 'Product Updated'),
        ('product.deleted', 'Product Deleted'),
    ]
    
    name = models.CharField(max_length=255, help_text='Friendly name for this webhook')
    target_url = models.URLField(max_length=500, help_text='URL to send webhook POST requests')
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_CHOICES,
        help_text='Event that triggers this webhook'
    )
    is_active = models.BooleanField(default=True, help_text='Enable or disable this webhook')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.event_type})"
