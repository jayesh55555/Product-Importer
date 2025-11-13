import csv
import os
from celery import shared_task
from django.db import transaction
from .models import Product


@shared_task(bind=True)
def process_csv_upload(self, file_path):
    """
    Process CSV file and import products into the database.
    Supports up to 500,000 rows with progress tracking.
    """
    try:
        # Update state to parsing
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 0,
                'status': 'Opening CSV file...'
            }
        )
        
        # First pass: count total rows
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            total_rows = sum(1 for row in csvfile) - 1  # Exclude header
        
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': total_rows,
                'status': f'Found {total_rows} products to process...'
            }
        )
        
        # Process in batches for efficiency
        batch_size = 1000
        products_to_create = []
        products_to_update = []
        existing_skus = {}
        
        # Get all existing SKUs (case-insensitive)
        for product in Product.objects.all():
            existing_skus[product.sku.upper()] = product
        
        with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Validate CSV headers
            required_fields = {'sku', 'name', 'description', 'active'}
            csv_fields = {field.lower().strip() for field in reader.fieldnames}
            
            if not required_fields.issubset(csv_fields):
                missing = required_fields - csv_fields
                raise ValueError(f'Missing required CSV columns: {", ".join(missing)}')
            
            current_row = 0
            
            for row in reader:
                current_row += 1
                
                # Update progress every 100 rows
                if current_row % 100 == 0:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': current_row,
                            'total': total_rows,
                            'status': f'Processing row {current_row} of {total_rows}...'
                        }
                    )
                
                # Parse row data
                sku = row.get('sku', '').strip().upper()
                name = row.get('name', '').strip()
                description = row.get('description', '').strip()
                active_str = row.get('active', '').strip().lower()
                
                # Skip empty rows
                if not sku or not name:
                    continue
                
                # Parse active field
                active = active_str in ('true', '1', 'yes', 'active')
                
                # Check if product exists (case-insensitive)
                if sku in existing_skus:
                    # Update existing product
                    product = existing_skus[sku]
                    product.name = name
                    product.description = description
                    product.active = active
                    products_to_update.append(product)
                else:
                    # Create new product
                    product = Product(
                        sku=sku,
                        name=name,
                        description=description,
                        active=active
                    )
                    products_to_create.append(product)
                    existing_skus[sku] = product
                
                # Process batch
                if len(products_to_create) + len(products_to_update) >= batch_size:
                    with transaction.atomic():
                        if products_to_create:
                            Product.objects.bulk_create(products_to_create, ignore_conflicts=False)
                        if products_to_update:
                            Product.objects.bulk_update(
                                products_to_update,
                                ['name', 'description', 'active', 'updated_at']
                            )
                    
                    products_to_create = []
                    products_to_update = []
            
            # Process remaining products
            if products_to_create or products_to_update:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': current_row,
                        'total': total_rows,
                        'status': 'Saving final batch to database...'
                    }
                )
                
                with transaction.atomic():
                    if products_to_create:
                        Product.objects.bulk_create(products_to_create, ignore_conflicts=False)
                    if products_to_update:
                        Product.objects.bulk_update(
                            products_to_update,
                            ['name', 'description', 'active', 'updated_at']
                        )
        
        # Clean up the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            'current': total_rows,
            'total': total_rows,
            'status': 'Import completed successfully!',
            'result': f'Processed {total_rows} products'
        }
        
    except Exception as e:
        # Clean up the uploaded file on error
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass  # Ignore cleanup errors
        
        # Don't manually set FAILURE state - let Celery handle it automatically
        # Just raise the exception and Celery will properly store it
        raise



@shared_task
def send_webhook_test(target_url, webhook_name):
    """
    Send a test webhook with sample payload.
    """
    import requests
    from datetime import datetime
    
    payload = {
        'event': 'webhook.test',
        'webhook_name': webhook_name,
        'timestamp': datetime.now().isoformat(),
        'data': {
            'message': 'This is a test webhook',
            'test': True
        }
    }
    
    try:
        response = requests.post(
            target_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return f'{response.status_code} {response.reason}'
    except requests.exceptions.RequestException as e:
        return f'Error: {str(e)}'


@shared_task
def send_webhook(target_url, event_type, product_data):
    """
    Send webhook notification for product events.
    """
    import requests
    from datetime import datetime
    
    payload = {
        'event': event_type,
        'timestamp': datetime.now().isoformat(),
        'data': product_data
    }
    
    try:
        response = requests.post(
            target_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return {
            'success': True,
            'status_code': response.status_code,
            'url': target_url
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': str(e),
            'url': target_url
        }
