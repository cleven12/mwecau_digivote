# MWECAU Voting System - Security & Licensing Guide

## Table of Contents
1. [Source Code Protection](#source-code-protection)
2. [Python Code Obfuscation](#python-code-obfuscation)
3. [Licensing Strategy](#licensing-strategy)
4. [Deployment Security](#deployment-security)
5. [Branch Management](#branch-management)
6. [Implementation Steps](#implementation-steps)

---

## 1. SOURCE CODE PROTECTION

### 1.1 Making Your Repl Private

**⚠️ CRITICAL: Public Repls expose source code under MIT License**

To protect your source code:

1. **Get Replit Core Membership**
   - Required for private Repls
   - Cost: ~$20/month
   - Go to: https://replit.com/pricing

2. **Make Repl Private**
   - Click on your Repl name
   - Go to Settings
   - Change visibility to "Private"
   - Only you can view/edit the code

3. **Add Custom License**
   Once private, add your proprietary license as a comment in main files or create `LICENSE.txt`:

```text
PROPRIETARY LICENSE - MWECAU VOTING SYSTEM

Copyright (c) 2025 [Your Name/Organization]

This software and associated documentation files (the "Software") are 
proprietary and confidential.

RESTRICTIONS:
1. No person or organization may use this Software without explicit 
   written permission from the copyright holder.
2. Redistribution, modification, or reverse engineering is strictly prohibited.
3. This Software is licensed only to authorized educational institutions 
   with a valid license agreement.
4. Unauthorized use will result in legal action.

For licensing inquiries, contact: [your-email@example.com]
```

### 1.2 Deployment Protection

**Important:** Even with private Repls, deployed apps are accessible. You need:

1. **Private Deployment** (Replit Teams Pro)
   - Restricts access to organization members only
   - Requires Teams Pro subscription
   - Best for internal use only

2. **Authentication Layer** (Implemented)
   - Your system already has JWT authentication
   - All sensitive endpoints require login
   - Good for public deployments

---

## 2. PYTHON CODE OBFUSCATION

Since Python is interpreted, source code is readable. Here are obfuscation options:

### 2.1 Option 1: PyArmor (Recommended)

**Installation:**
```bash
pip install pyarmor
```

**Obfuscate your code:**
```bash
# Obfuscate all Python files
pyarmor gen -r -O dist/ .

# This creates obfuscated .pyc files in dist/
# Original .py files remain readable
```

**Features:**
- Strong obfuscation (bytecode encryption)
- License key support (limit users/devices)
- Expiration dates for licenses
- Hardware binding

**Example license configuration:**
```bash
# Create license that expires in 1 year
pyarmor gen --with-license licenses/license.lic \
            --bind-expire 2026-10-23 \
            -O dist/ .
```

**Limitations:**
- Requires PyArmor runtime on client
- Annual license cost for commercial use (~$299)
- Performance overhead (~5-10%)

### 2.2 Option 2: Cython Compilation

Compile Python to C extensions (.so files):

```bash
# Install Cython
pip install cython

# Create setup.py
cat > setup.py << 'EOF'
from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize([
        "core/**/*.py",
        "election/**/*.py",
        "mw_es/**/*.py"
    ]),
)
EOF

# Compile to .so files (not human-readable)
python setup.py build_ext --inplace
```

**Features:**
- Source code becomes binary (.so files)
- Performance improvement (10-30% faster)
- Free and open-source

**Limitations:**
- Platform-specific (must compile for Linux/Windows/Mac separately)
- Harder to debug
- Some Python features may not work

### 2.3 Option 3: PyInstaller Bundling

Bundle everything into executable:

```bash
pip install pyinstaller

# Create standalone executable
pyinstaller --onefile --name mwecau-voting manage.py
```

**Features:**
- Single executable file
- Harder to reverse engineer
- No Python installation needed on client

**Limitations:**
- Large file size (50-100MB+)
- Not suitable for web deployments
- Can still be decompiled with effort

### 2.4 Recommended Approach for Your System

**BEST OPTION: Private Repl + License Authentication**

Don't obfuscate the code. Instead:

1. **Keep Repl Private** (requires Replit Core)
2. **Add License Key System** (see Section 3)
3. **Use Deployment Security** (see Section 4)

**Why?**
- Python obfuscation is easily defeated
- License keys are more effective
- Easier to maintain and debug
- Better customer experience

---

## 3. LICENSING STRATEGY

### 3.1 Implement License Key System

Add this to your Django app:

**Step 1: Create License Model**
```python
# core/models.py (add this)
from django.db import models
from django.utils import timezone

class OrganizationLicense(models.Model):
    organization_name = models.CharField(max_length=200)
    license_key = models.CharField(max_length=100, unique=True)
    contact_email = models.EmailField()
    max_users = models.IntegerField(default=1000)
    expiry_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        return (
            self.is_active and 
            self.expiry_date > timezone.now()
        )
    
    def __str__(self):
        return f"{self.organization_name} - {self.license_key}"
```

**Step 2: Create Middleware for License Check**
```python
# core/middleware.py (create this file)
from django.http import JsonResponse
from django.conf import settings
from .models import OrganizationLicense

class LicenseCheckMiddleware:
    """Check if system has valid license before allowing access."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = [
            '/admin/',
            '/api/auth/login/',
            '/swagger/',
            '/redoc/',
        ]
    
    def __call__(self, request):
        # Skip license check for exempt paths
        if any(request.path.startswith(path) for path in self.exempt_paths):
            return self.get_response(request)
        
        # Skip check in development
        if settings.DEBUG and getattr(settings, 'SKIP_LICENSE_CHECK', True):
            return self.get_response(request)
        
        # Check for valid license
        valid_license = OrganizationLicense.objects.filter(
            is_active=True,
            expiry_date__gt=timezone.now()
        ).exists()
        
        if not valid_license:
            return JsonResponse({
                'error': 'No valid license found',
                'message': 'This system requires a valid organizational license. Contact the administrator.',
                'contact': 'licensing@mwecau.ac.tz'
            }, status=403)
        
        return self.get_response(request)
```

**Step 3: Add to Settings**
```python
# mw_es/settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.LicenseCheckMiddleware',  # ADD THIS
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# For production, set this to False
SKIP_LICENSE_CHECK = True  # Set to False when deploying
```

**Step 4: Create License Management Command**
```python
# core/management/commands/create_license.py
from django.core.management.base import BaseCommand
from core.models import OrganizationLicense
from django.utils import timezone
from datetime import timedelta
import secrets

class Command(BaseCommand):
    help = 'Create a new organization license'
    
    def add_arguments(self, parser):
        parser.add_argument('--org', type=str, required=True)
        parser.add_argument('--email', type=str, required=True)
        parser.add_argument('--max-users', type=int, default=1000)
        parser.add_argument('--years', type=int, default=1)
    
    def handle(self, *args, **options):
        license_key = f"MWECAU-{secrets.token_hex(16).upper()}"
        expiry = timezone.now() + timedelta(days=365 * options['years'])
        
        license = OrganizationLicense.objects.create(
            organization_name=options['org'],
            license_key=license_key,
            contact_email=options['email'],
            max_users=options['max_users'],
            expiry_date=expiry
        )
        
        self.stdout.write(self.style.SUCCESS(
            f"\nLicense created successfully!\n"
            f"Organization: {license.organization_name}\n"
            f"License Key: {license.license_key}\n"
            f"Max Users: {license.max_users}\n"
            f"Expires: {license.expiry_date}\n"
        ))
```

**Usage:**
```bash
# Create license for an organization
python manage.py create_license \
    --org "Mwenge Catholic University" \
    --email "admin@mwecau.ac.tz" \
    --max-users 5000 \
    --years 1

# Output: MWECAU-A1B2C3D4E5F67890ABCDEF1234567890
```

### 3.2 License Activation System

Add endpoint for license activation:

```python
# core/views.py (add this)
class ActivateLicenseView(APIView):
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        license_key = request.data.get('license_key')
        
        try:
            license = OrganizationLicense.objects.get(license_key=license_key)
            
            if license.is_valid():
                return Response({
                    'status': 'success',
                    'message': 'License activated',
                    'organization': license.organization_name,
                    'expires': license.expiry_date
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'License expired or inactive'
                }, status=400)
        except OrganizationLicense.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Invalid license key'
            }, status=404)
```

---

## 4. DEPLOYMENT SECURITY

### 4.1 Secure Environment Variables

Never commit these to Git:

```bash
# .env (create this file)
DJANGO_SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@host:5432/db
EMAIL_HOST_PASSWORD=your-email-password
LICENSE_CHECK_ENABLED=True
```

Update settings.py:
```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'fallback-key-for-dev')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
```

### 4.2 Production Deployment Checklist

Before deploying:

```python
# mw_es/settings.py - Production settings
DEBUG = False  # NEVER True in production
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Enable license check
SKIP_LICENSE_CHECK = False
```

### 4.3 Database Security

```python
# Use PostgreSQL in production (not SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': '5432',
    }
}
```

---

## 5. BRANCH MANAGEMENT

### 5.1 Creating Branches in Replit

**Using Replit Interface:**
1. Open Git pane (Tools → Git)
2. Click branch dropdown next to current branch name
3. Click "Create new branch"
4. Name it (e.g., `production`, `obfuscated`, `client-deploy`)

**Using Command Line:**
```bash
# Create new branch for obfuscated code
git checkout -b obfuscated-production

# Create branch for specific client
git checkout -b client-university-x

# Push to remote
git push origin obfuscated-production
```

### 5.2 Recommended Branch Strategy

```
main (development)
├── production (clean code with license check)
├── obfuscated (PyArmor protected)
└── client-branches/
    ├── mwecau-deploy
    ├── client-univ-a
    └── client-univ-b
```

### 5.3 Workflow

1. **Development:** Work on `main` branch
2. **Testing:** Merge to `production` branch
3. **Client Deployment:** Create client-specific branch from `production`
4. **Obfuscation:** If needed, create `obfuscated` branch with PyArmor

---

## 6. IMPLEMENTATION STEPS

### Option A: Maximum Security (Recommended)

```bash
# Step 1: Get Replit Core ($20/month)
# Step 2: Make Repl private
# Step 3: Implement license system (code provided above)
# Step 4: Deploy with license check enabled
# Step 5: Give each client their license key
```

**Cost:** $20/month + your time  
**Protection:** Very High  
**Maintenance:** Easy

### Option B: Code Obfuscation

```bash
# Step 1: Install PyArmor
pip install pyarmor

# Step 2: Create obfuscated branch
git checkout -b obfuscated-production

# Step 3: Obfuscate code
pyarmor gen -r -O dist/ .

# Step 4: Replace .py files with obfuscated versions
# Step 5: Add license keys
pyarmor gen --with-license licenses/client1.lic -O dist/ .

# Step 6: Deploy from dist/
```

**Cost:** $299/year (PyArmor Pro) for commercial use  
**Protection:** High  
**Maintenance:** Hard (need to recompile for each change)

### Option C: Both (Maximum Protection)

Combine both approaches:
1. Private Repl (source control)
2. License system (runtime protection)
3. PyArmor (code protection)

---

## 7. RECOMMENDED SOLUTION FOR YOUR CASE

Based on your requirements, I recommend:

### Phase 1: Immediate (Free)
1. ✅ Keep source code on private GitHub repo (or private Replit with Core)
2. ✅ Add license key system (code provided above)
3. ✅ Enable license check in production (`SKIP_LICENSE_CHECK = False`)
4. ✅ Use environment variables for secrets

### Phase 2: For Paying Clients (When Revenue Starts)
1. Get Replit Core ($20/month) → Make Repl private
2. Consider PyArmor Pro ($299/year) for extra protection
3. Use client-specific branches with their licenses

### Phase 3: For Enterprise Clients
1. Private deployment (Replit Teams Pro)
2. Custom domain
3. Dedicated database
4. SLA guarantees

---

## 8. PRICING YOUR SOLUTION

Suggested pricing model:

```
┌─────────────────────────────────────────────────┐
│ MWECAU Voting System - Licensing Tiers         │
├─────────────────────────────────────────────────┤
│ Basic License (Up to 1,000 users)              │
│ - 1 year license                                │
│ - Email support                                 │
│ - Standard updates                              │
│ Price: $500/year                                │
├─────────────────────────────────────────────────┤
│ Professional License (Up to 5,000 users)        │
│ - 1 year license                                │
│ - Priority email support                        │
│ - All updates                                   │
│ - Custom branding                               │
│ Price: $1,500/year                              │
├─────────────────────────────────────────────────┤
│ Enterprise License (Unlimited users)            │
│ - 1 year license                                │
│ - 24/7 support                                  │
│ - Private deployment                            │
│ - Custom features                               │
│ - Source code access (escrow)                   │
│ Price: $5,000/year                              │
└─────────────────────────────────────────────────┘
```

---

## 9. LEGAL PROTECTION

### 9.1 Terms of Service

Create `TERMS_OF_SERVICE.md`:

```markdown
# Terms of Service

By using this software, you agree to:

1. **License Requirement:** Valid license key required for operation
2. **No Reverse Engineering:** Prohibited to decompile or reverse engineer
3. **Data Privacy:** Your organization's data remains confidential
4. **Support:** Email support included with paid licenses
5. **Updates:** Receive updates during license period
6. **Termination:** License may be terminated for violations

For full terms, contact: legal@yourcompany.com
```

### 9.2 Client Agreement Template

```
SOFTWARE LICENSE AGREEMENT

Between: [Your Company Name]
And: [Client Organization]

Software: MWECAU Digital Voting System
License Key: MWECAU-XXXXXXXXXX
Duration: [Start Date] to [End Date]
Max Users: [Number]
Annual Fee: $[Amount]

Client agrees not to:
- Share license key
- Reverse engineer software
- Resell or redistribute

[Signatures]
```

---

## 10. NEXT STEPS

**To implement license system now:**

```bash
# 1. Add license model to migrations
python manage.py makemigrations
python manage.py migrate

# 2. Create middleware file
# (Copy code from Section 3.2 above)

# 3. Create first license for testing
python manage.py create_license \
    --org "Test Organization" \
    --email "test@example.com" \
    --years 1

# 4. Test with license check disabled (development)
SKIP_LICENSE_CHECK=True python manage.py runserver

# 5. Test with license check enabled (production simulation)
SKIP_LICENSE_CHECK=False python manage.py runserver
```

**For obfuscation:**
```bash
# Create separate branch
git checkout -b obfuscated

# Install PyArmor
pip install pyarmor

# Test obfuscation
pyarmor gen -r -O test_dist/ core/

# Check if it works
cd test_dist
python -m core.views  # Should work but code is obfuscated
```

---

## Summary

**BEST APPROACH:**
1. ✅ Make Repl Private (Replit Core - $20/month)
2. ✅ Add License Key System (provided code above)
3. ✅ Use environment variables for secrets
4. ✅ Create client-specific branches
5. ⚠️ Optional: PyArmor for extra protection ($299/year)

This gives you:
- Protected source code (private Repl)
- Usage control (license keys)
- Client management (branches)
- Revenue stream (annual licenses)
- Easy maintenance

**Questions? Contact me or refer to Django security documentation.**
