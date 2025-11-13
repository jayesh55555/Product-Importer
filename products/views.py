import os
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from celery.result import AsyncResult
from .models import Product, Webhook
from .forms import ProductForm, ProductFilterForm, WebhookForm
from .tasks import process_csv_upload


class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = Product.objects.all().order_by('-created_at')
        
        # Get filter parameters
        sku = self.request.GET.get('sku', '').strip()
        name = self.request.GET.get('name', '').strip()
        description = self.request.GET.get('description', '').strip()
        active = self.request.GET.get('active', '')
        
        # Apply filters
        if sku:
            queryset = queryset.filter(sku__icontains=sku)
        
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        if description:
            queryset = queryset.filter(description__icontains=description)
        
        if active == 'true':
            queryset = queryset.filter(active=True)
        elif active == 'false':
            queryset = queryset.filter(active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the filter form to the template
        context['filter_form'] = ProductFilterForm(self.request.GET)
        # Preserve query parameters for pagination
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            query_params.pop('page')
        context['query_string'] = query_params.urlencode()
        return context


class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('products:product_list')


def csv_upload_page(request):
    """Render the CSV upload page."""
    return render(request, 'products/upload.html')


@csrf_exempt
@require_http_methods(["POST"])
def start_upload_task(request):
    """
    Handle CSV file upload and start the Celery task.
    Returns the task_id for progress tracking.
    """
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    uploaded_file = request.FILES['file']
    
    # Validate file extension
    if not uploaded_file.name.endswith('.csv'):
        return JsonResponse({'error': 'Only CSV files are allowed'}, status=400)
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join(settings.BASE_DIR, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file temporarily
    file_path = os.path.join(upload_dir, f'upload_{uploaded_file.name}')
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    
    # Start the Celery task
    task = process_csv_upload.delay(file_path)
    
    return JsonResponse({
        'task_id': task.id,
        'status': 'Task started'
    })


@require_http_methods(["GET"])
def get_upload_progress(request, task_id):
    """
    Get the progress of a CSV upload task.
    Always returns valid JSON, even on errors.
    """
    try:
        task = AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': 'PENDING',
                'current': 0,
                'total': 0,
                'status': 'Task is pending...',
                'details': {}
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': 'PROGRESS',
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 0),
                'status': task.info.get('status', 'Processing...'),
                'details': {}
            }
        elif task.state == 'SUCCESS':
            response = {
                'state': 'SUCCESS',
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 0),
                'status': task.info.get('status', 'Completed!'),
                'result': task.info.get('result', 'Import completed successfully'),
                'details': {}
            }
        elif task.state == 'FAILURE':
            # Extract error details from task.info
            exc_type = ''
            exc_message = 'An unknown error occurred'
            
            if isinstance(task.info, dict):
                # Our custom error format with exc_type and exc_message
                exc_type = task.info.get('exc_type', '')
                exc_message = task.info.get('exc_message', task.info.get('error', str(task.info)))
            elif isinstance(task.info, Exception):
                # Standard exception
                exc_type = task.info.__class__.__name__
                exc_message = str(task.info)
            else:
                # Fallback
                exc_message = str(task.info)
            
            response = {
                'state': 'FAILURE',
                'current': 0,
                'total': 0,
                'status': 'Task failed',
                'details': {
                    'exc_type': exc_type,
                    'exc_message': exc_message
                }
            }
        else:
            # Handle any other unexpected states
            response = {
                'state': task.state,
                'current': 0,
                'total': 0,
                'status': f'Task state: {task.state}',
                'details': {}
            }
        
        return JsonResponse(response)
        
    except Exception as e:
        # Catch any unexpected errors and return valid JSON
        return JsonResponse({
            'state': 'FAILURE',
            'current': 0,
            'total': 0,
            'status': 'Error checking task status',
            'details': {
                'exc_type': e.__class__.__name__,
                'exc_message': str(e)
            }
        })


def bulk_delete_products(request):
    """
    Bulk delete all products with confirmation step.
    GET: Show confirmation page
    POST: Delete all products
    """
    if request.method == 'POST':
        # Get the count before deletion
        count = Product.objects.count()
        
        # Delete all products
        Product.objects.all().delete()
        
        # Redirect to product list with success message
        from django.contrib import messages
        messages.success(request, f'Successfully deleted {count} products.')
        return render(request, 'products/bulk_delete_success.html', {'count': count})
    
    # GET request - show confirmation page
    product_count = Product.objects.count()
    return render(request, 'products/bulk_delete_confirm.html', {'product_count': product_count})



# Webhook Views
class WebhookListView(ListView):
    model = Webhook
    template_name = 'products/webhook_list.html'
    context_object_name = 'webhooks'
    paginate_by = 50


class WebhookCreateView(CreateView):
    model = Webhook
    form_class = WebhookForm
    template_name = 'products/webhook_form.html'
    success_url = reverse_lazy('products:webhook_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context


class WebhookUpdateView(UpdateView):
    model = Webhook
    form_class = WebhookForm
    template_name = 'products/webhook_form.html'
    success_url = reverse_lazy('products:webhook_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context


class WebhookDeleteView(DeleteView):
    model = Webhook
    template_name = 'products/webhook_confirm_delete.html'
    success_url = reverse_lazy('products:webhook_list')


def test_webhook(request, pk):
    """Test a webhook by sending a sample payload."""
    from .tasks import send_webhook_test
    from .models import Webhook
    
    webhook = Webhook.objects.get(pk=pk)
    
    # Send test webhook asynchronously
    task = send_webhook_test.delay(webhook.target_url, webhook.name)
    
    # Wait for result (with timeout)
    try:
        result = task.get(timeout=10)
        from django.contrib import messages
        messages.success(request, f'Test sent to {webhook.name}. Response: {result}')
    except Exception as e:
        from django.contrib import messages
        messages.error(request, f'Test failed: {str(e)}')
    
    return render(request, 'products/webhook_test_result.html', {
        'webhook': webhook,
        'result': result if 'result' in locals() else str(e)
    })
