# MWECAU Election Platform - Backend Development Guide

A comprehensive guide for developing the backend API for the MWECAU Election Platform using Django and Django REST Framework.

## 📋 Table of Contents

- [Overview](#overview)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Creating New Features](#creating-new-features)
- [Database Operations](#database-operations)
- [API Development](#api-development)
- [Testing Guide](#testing-guide)
- [Git Workflow](#git-workflow)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This guide will walk you through the complete backend development process for the MWECAU Election Platform, from initial setup to deploying your changes.

## 🛠 Technology Stack

- **Django 4.2+** - Web framework
- **Django REST Framework** - API development
- **Python 3.8+** - Programming language
- **PostgreSQL/MySQL/SQLite** - Database options
- **Git** - Version control

## 🚀 Getting Started

### Step 1: Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/mwecau-ict-club/mwecau_election_platform.git
   cd mwecau_election_platform/src/backend
   ```

2. **Create virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate it
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env file with your settings
   nano .env  # or use any text editor
   ```

5. **Database setup**
   ```bash
   # Run migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   ```

6. **Test the setup**
   ```bash
   python manage.py runserver
   ```
   Visit `http://localhost:8000` to confirm everything works.

## 💻 Development Workflow

### Daily Development Process

1. **Start your day**
   ```bash
   # Activate virtual environment
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Pull latest changes
   git pull origin main
   
   # Start development server
   python manage.py runserver
   ```

2. **Check for updates**
   ```bash
   # Check if new dependencies were added
   pip install -r requirements.txt
   
   # Apply any new migrations
   python manage.py migrate
   ```

## 📁 Project Structure

```
backend/
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
├── .env                        # Your environment variables (create this)
├── db.sqlite3                  # SQLite database (auto-generated)
├── mwecau_election/            # Main project directory
│   ├── __init__.py
│   ├── settings.py             # Django settings
│   ├── urls.py                 # URL routing
│   └── wsgi.py                 # WSGI configuration
├── apps/                       # Application modules
│   ├── authentication/         # User authentication
│   ├── elections/             # Election management
│   ├── candidates/            # Candidate management
│   ├── voting/                # Voting system
│   └── results/               # Results processing
├── static/                     # Static files (CSS, JS, images)
├── media/                      # User uploaded files
└── templates/                  # HTML templates
```

## 🆕 Creating New Features

### Step 1: Create a Feature Branch

```bash
# Create and switch to new branch
git checkout -b feature/your-feature-name

# Examples:
git checkout -b feature/candidate-approval
git checkout -b feature/email-notifications
git checkout -b bugfix/voting-validation
```

### Step 2: Create a New Django App (if needed)

```bash
# Create new Django app
python manage.py startapp your_app_name

# Example:
python manage.py startapp notifications
```

### Step 3: Add App to Settings

Edit `mwecau_election/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    
    # Your apps
    'apps.authentication',
    'apps.elections',
    'apps.candidates',
    'apps.voting',
    'apps.results',
    'apps.notifications',  # Add your new app here
]
```

### Step 4: Create Models

Edit `apps/your_app/models.py`:

```python
from django.db import models
from django.contrib.auth.models import User

class YourModel(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Your Model"
        verbose_name_plural = "Your Models"
        ordering = ['-created_at']
```

### Step 5: Create and Apply Migrations

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### Step 6: Create API Serializers

Create `apps/your_app/serializers.py`:

```python
from rest_framework import serializers
from .models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YourModel
        fields = ['id', 'title', 'description', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
```

### Step 7: Create API Views

Edit `apps/your_app/views.py`:

```python
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import YourModel
from .serializers import YourModelSerializer

class YourModelViewSet(viewsets.ModelViewSet):
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Filter based on user permissions
        if self.request.user.is_superuser:
            return YourModel.objects.all()
        return YourModel.objects.filter(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        # Custom endpoint logic
        obj = self.get_object()
        # Your custom logic here
        return Response({'status': 'success'})
```

### Step 8: Configure URLs

Create `apps/your_app/urls.py`:

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import YourModelViewSet

router = DefaultRouter()
router.register(r'your-models', YourModelViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
```

Add to main `mwecau_election/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.your_app.urls')),  # Add this line
]
```

### Step 9: Register in Admin (Optional)

Edit `apps/your_app/admin.py`:

```python
from django.contrib import admin
from .models import YourModel

@admin.register(YourModel)
class YourModelAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
```

## 🗄️ Database Operations

### Common Database Commands

```bash
# Create new migration after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset migrations (BE CAREFUL!)
python manage.py migrate your_app zero
python manage.py migrate

# Check database schema
python manage.py dbshell

# Create database backup
python manage.py dumpdata > backup.json

# Restore from backup
python manage.py loaddata backup.json
```

### Working with Data

```bash
# Open Django shell
python manage.py shell

# Example shell commands:
>>> from apps.elections.models import Election
>>> from django.contrib.auth.models import User

# Create data
>>> user = User.objects.get(username='admin')
>>> election = Election.objects.create(
...     title='Student Council Election',
...     description='Annual student council election',
...     created_by=user
... )

# Query data
>>> elections = Election.objects.all()
>>> active_elections = Election.objects.filter(is_active=True)
```

## 🔌 API Development

### Testing Your API

1. **Using Django Admin**
   ```bash
   # Access admin interface
   http://localhost:8000/admin/
   ```

2. **Using curl**
   ```bash
   # GET request
   curl -H "Authorization: Token your-token" http://localhost:8000/api/elections/
   
   # POST request
   curl -X POST \
     -H "Authorization: Token your-token" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Election","description":"Test"}' \
     http://localhost:8000/api/elections/
   ```

3. **Using Python requests**
   ```python
   import requests
   
   headers = {'Authorization': 'Token your-token'}
   response = requests.get('http://localhost:8000/api/elections/', headers=headers)
   print(response.json())
   ```

## 🧪 Testing Guide

### Step 1: Write Tests

Create tests in `apps/your_app/tests.py`:

```python
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import YourModel

class YourModelTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_model(self):
        url = '/api/your-models/'
        data = {
            'title': 'Test Title',
            'description': 'Test Description'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(YourModel.objects.count(), 1)
    
    def test_list_models(self):
        YourModel.objects.create(
            title='Test',
            description='Test',
            created_by=self.user
        )
        url = '/api/your-models/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
```

### Step 2: Run Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.your_app

# Run with verbosity
python manage.py test --verbosity=2

# Run specific test
python manage.py test apps.your_app.tests.YourModelTestCase.test_create_model
```

## 📝 Git Workflow

### Step 1: Check Status

```bash
# Check what files have changed
git status

# See specific changes
git diff

# See changes in specific file
git diff apps/elections/models.py
```

### Step 2: Add Changes

```bash
# Add specific files
git add apps/elections/models.py
git add apps/elections/views.py

# Add all files in a directory
git add apps/elections/

# Add all changes
git add .

# Interactive add (recommended)
git add -i
```

### Step 3: Commit Changes

```bash
# Commit with message
git commit -m "Add candidate approval functionality"

# Better commit message format:
git commit -m "feat: add candidate approval workflow

- Add approval status field to Candidate model
- Create API endpoint for approval actions
- Add admin interface for candidate management
- Include email notifications for approval status"
```

### Step 4: Push Changes

```bash
# Push to your feature branch
git push origin feature/your-feature-name

# If first time pushing this branch
git push -u origin feature/your-feature-name
```

### Step 5: Create Pull Request

1. Go to GitHub repository
2. Click "Compare & pull request"
3. Fill out the PR template:

```markdown
## Description
Brief description of changes

## Changes Made
- [ ] Added new model for notifications
- [ ] Created API endpoints
- [ ] Added tests
- [ ] Updated documentation

## Testing
- [ ] Unit tests pass
- [ ] Manual testing completed
- [ ] No breaking changes

## Screenshots (if applicable)
[Add screenshots of UI changes]
```

### Step 6: After PR is Merged

```bash
# Switch back to main branch
git checkout main

# Pull the latest changes
git pull origin main

# Delete your feature branch
git branch -d feature/your-feature-name

# Delete remote branch (optional)
git push origin --delete feature/your-feature-name
```

## 🚀 Deployment

### Environment Setup

1. **Create production environment file**
   ```bash
   cp .env.example .env.production
   # Edit with production settings
   ```

2. **Install production dependencies**
   ```bash
   pip install gunicorn
   pip freeze > requirements.txt
   ```

3. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

### Using Docker (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "mwecau_election.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Build and run:

```bash
docker build -t mwecau-backend .
docker run -p 8000:8000 mwecau-backend
```

## 🔧 Troubleshooting

### Common Issues and Solutions

1. **Migration conflicts**
   ```bash
   # Reset migrations
   python manage.py migrate your_app zero
   rm apps/your_app/migrations/0001_initial.py
   python manage.py makemigrations your_app
   python manage.py migrate
   ```

2. **Port already in use**
   ```bash
   # Use different port
   python manage.py runserver 8001
   
   # Or kill process using port 8000
   sudo lsof -t -i tcp:8000 | xargs kill -9
   ```

3. **Virtual environment issues**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Database locked**
   ```bash
   # For SQLite
   rm db.sqlite3
   python manage.py migrate
   ```

### Getting Help

- **Email**: mwecauictclub@gmail.com
- **GitHub Issues**: [Create an issue](https://github.com/mwecau-ict-club/mwecau_election_platform/issues)
- **Check logs**: Always check Django console output for error details

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Git Documentation](https://git-scm.com/doc)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)

---

**Next Steps**: After setting up the backend, integrate with the [Frontend](../frontend/README.md) or deploy the [Full-stack application](../full_stack/README.md).