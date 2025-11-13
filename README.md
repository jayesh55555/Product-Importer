# Product Importer

A Django-based product management system with CSV import, webhooks, and async processing capabilities.

## Features

- **Product Management**: Full CRUD operations for products with SKU, name, description, and active status
- **CSV Import**: Async bulk import of up to 500,000 products with real-time progress tracking
- **Webhooks**: Configure webhooks to receive notifications on product create/update/delete events
- **Bulk Operations**: Bulk delete all products with confirmation
- **Filtering & Pagination**: Filter products by SKU, name, description, and status with 50 items per page
- **Case-Insensitive SKU**: Unique SKU handling with case-insensitive matching

## Tech Stack

- **Backend**: Django 4.2
- **Database**: PostgreSQL
- **Task Queue**: Celery with Redis
- **Frontend**: Bootstrap 5
- **Deployment**: Render (or any platform supporting Python/PostgreSQL/Redis)

## Prerequisites

- Python 3.12+
- PostgreSQL 12+
- Redis 6+

## Local Development Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd product_importer
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://postgres:password@localhost:5432/product_importer_db
REDIS_URL=redis://localhost:6379/0
```

### 5. Set up PostgreSQL database

```sql
CREATE DATABASE product_importer_db;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE product_importer_db TO postgres;
```

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Create superuser

```bash
python manage.py createsuperuser
```

### 8. Collect static files

```bash
python manage.py collectstatic --noinput
```

## Running the Application

You need to run three separate processes:

### Terminal 1: Django Development Server

```bash
python manage.py runserver
```

Access the application at: `http://localhost:8000`

### Terminal 2: Redis Server

**Windows (WSL):**
```bash
wsl
redis-server
```

**Linux/Mac:**
```bash
redis-server
```

### Terminal 3: Celery Worker

```bash
celery -A product_importer worker --loglevel=info --pool=solo
```

Note: Use `--pool=solo` on Windows. On Linux/Mac, you can omit this flag.

## Usage

### Product Management

1. Navigate to `http://localhost:8000/products/`
2. Use the interface to:
   - Add new products
   - Edit existing products
   - Delete products
   - Filter and search products

### CSV Import

1. Navigate to `http://localhost:8000/products/upload/`
2. Upload a CSV file with the following format:

```csv
sku,name,description,active
PROD001,Product Name,Product Description,true
PROD002,Another Product,Another Description,false
```

**CSV Requirements:**
- Required columns: `sku`, `name`, `description`, `active`
- Active field: use `true`, `false`, `1`, `0`, `yes`, or `no`
- If a product with the same SKU exists, it will be updated
- Maximum 500,000 rows supported

3. Monitor real-time progress as the import processes

### Webhooks

1. Navigate to `http://localhost:8000/products/webhooks/`
2. Create a new webhook:
   - **Name**: Friendly name (e.g., "Slack Notification")
   - **Target URL**: Endpoint to receive webhook POST requests
   - **Event Type**: Choose from:
     - `product.created` - Triggered when a product is created
     - `product.updated` - Triggered when a product is updated
     - `product.deleted` - Triggered when a product is deleted
   - **Active**: Enable/disable the webhook

3. Test webhooks using the "Test" button

**Webhook Payload Example:**
```json
{
  "event": "product.created",
  "timestamp": "2025-11-13T12:00:00",
  "data": {
    "id": 1,
    "sku": "PROD001",
    "name": "Product Name",
    "description": "Product Description",
    "active": true,
    "created_at": "2025-11-13T12:00:00",
    "updated_at": "2025-11-13T12:00:00"
  }
}
```

### Bulk Delete

1. Navigate to `http://localhost:8000/products/`
2. Click "Bulk Delete All" button
3. Confirm the action (requires checkbox confirmation)
4. All products will be permanently deleted

## Admin Panel

Access the Django admin at: `http://localhost:8000/admin/`

Use your superuser credentials to:
- Manage products
- Configure webhooks
- View all data

## API Endpoints

### Products
- `GET /products/` - List products (with filtering and pagination)
- `GET /products/create/` - Create product form
- `POST /products/create/` - Create product
- `GET /products/<id>/update/` - Edit product form
- `POST /products/<id>/update/` - Update product
- `GET /products/<id>/delete/` - Delete confirmation
- `POST /products/<id>/delete/` - Delete product

### CSV Upload
- `GET /products/upload/` - Upload page
- `POST /products/upload/start/` - Start upload task
- `GET /products/upload/progress/<task_id>/` - Get upload progress

### Webhooks
- `GET /products/webhooks/` - List webhooks
- `GET /products/webhooks/create/` - Create webhook form
- `POST /products/webhooks/create/` - Create webhook
- `GET /products/webhooks/<id>/update/` - Edit webhook form
- `POST /products/webhooks/<id>/update/` - Update webhook
- `GET /products/webhooks/<id>/delete/` - Delete confirmation
- `POST /products/webhooks/<id>/delete/` - Delete webhook
- `GET /products/webhooks/<id>/test/` - Test webhook

### Bulk Operations
- `GET /products/bulk-delete/` - Bulk delete confirmation
- `POST /products/bulk-delete/` - Execute bulk delete

## Live Demo

This project is also deployed on Render for demonstration purposes:
https://product-importer-web-u1nn.onrender.com/products

## Project Structure

```
product_importer/
├── product_importer/          # Project settings
│   ├── settings.py           # Django settings (production-ready)
│   ├── celery.py            # Celery configuration
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py              # WSGI application
├── products/                 # Main app
│   ├── models.py            # Product and Webhook models
│   ├── views.py             # All views (CRUD, upload, webhooks)
│   ├── forms.py             # Django forms
│   ├── tasks.py             # Celery tasks
│   ├── signals.py           # Django signals for webhooks
│   ├── urls.py              # App URL patterns
│   ├── admin.py             # Admin configuration
│   ├── templates/           # HTML templates
│   └── migrations/          # Database migrations
├── requirements.txt          # Python dependencies
├── Procfile                 # Render deployment config
├── render.yaml              # Render infrastructure config
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Troubleshooting

### Celery not picking up tasks

1. Restart Celery worker
2. Clear Redis: `redis-cli FLUSHDB`
3. Check Celery is running: `celery -A product_importer inspect active`

### CSV upload fails

1. Check CSV format matches requirements
2. Verify all required columns are present
3. Check Celery worker logs for errors
4. Ensure Redis is running

### Webhooks not firing

1. Verify webhook is marked as "Active"
2. Check Celery worker is running
3. Test webhook using "Test" button
4. Check target URL is accessible

### Database connection errors

1. Verify PostgreSQL is running
2. Check database credentials in `.env`
3. Ensure database exists: `CREATE DATABASE product_importer_db;`

## Development

### Running tests

```bash
python manage.py test
```

### Creating new migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Checking for issues

```bash
python manage.py check
```

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
