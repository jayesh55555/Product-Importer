from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, Webhook
from .tasks import send_webhook


@receiver(post_save, sender=Product)
def product_saved(sender, instance, created, **kwargs):
    """
    Trigger webhooks when a product is created or updated.
    """
    # Determine event type
    event_type = 'product.created' if created else 'product.updated'
    
    # Get all active webhooks for this event
    webhooks = Webhook.objects.filter(event_type=event_type, is_active=True)
    
    # Prepare product data
    product_data = {
        'id': instance.id,
        'sku': instance.sku,
        'name': instance.name,
        'description': instance.description,
        'active': instance.active,
        'created_at': instance.created_at.isoformat(),
        'updated_at': instance.updated_at.isoformat(),
    }
    
    # Send webhook for each configured endpoint
    for webhook in webhooks:
        send_webhook.delay(webhook.target_url, event_type, product_data)


@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    """
    Trigger webhooks when a product is deleted.
    """
    event_type = 'product.deleted'
    
    # Get all active webhooks for this event
    webhooks = Webhook.objects.filter(event_type=event_type, is_active=True)
    
    # Prepare product data (limited since object is being deleted)
    product_data = {
        'id': instance.id,
        'sku': instance.sku,
        'name': instance.name,
    }
    
    # Send webhook for each configured endpoint
    for webhook in webhooks:
        send_webhook.delay(webhook.target_url, event_type, product_data)
