from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('upload/', views.csv_upload_page, name='csv_upload'),
    path('upload/start/', views.start_upload_task, name='start_upload'),
    path('upload/progress/<str:task_id>/', views.get_upload_progress, name='upload_progress'),
    path('bulk-delete/', views.bulk_delete_products, name='bulk_delete'),
    # Webhook URLs
    path('webhooks/', views.WebhookListView.as_view(), name='webhook_list'),
    path('webhooks/create/', views.WebhookCreateView.as_view(), name='webhook_create'),
    path('webhooks/<int:pk>/update/', views.WebhookUpdateView.as_view(), name='webhook_update'),
    path('webhooks/<int:pk>/delete/', views.WebhookDeleteView.as_view(), name='webhook_delete'),
    path('webhooks/<int:pk>/test/', views.test_webhook, name='webhook_test'),
]
