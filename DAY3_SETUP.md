# Day 3: OCR, Async, Caching - Setup & Running Guide

## 🎯 What Was Implemented

### 1. **Celery + Redis Setup**
- Celery configured for async task processing
- Redis as message broker and result backend
- Async task: `run_analysis_task` for background processing

### 2. **OCR Pipeline**
- Image upload support with Tesseract OCR
- Text extraction from ingredient label images
- Graceful error handling when OCR fails or Tesseract unavailable

### 3. **Caching Layer**
- Redis caching for ingredient lookup results
- 24-hour cache TTL to prevent recomputation
- Both list-level and individual ingredient caching

### 4. **Tests**
- Unit tests for OCR service with mocks
- Async task tests
- Integration tests for image upload workflow

---

## 🚀 Setup Instructions

### Prerequisites
1. **Redis Server**
   ```powershell
   # Install Redis on Windows (via Chocolatey)
   choco install redis-64
   
   # Or download from: https://github.com/microsoftarchive/redis/releases
   # Start Redis server:
   redis-server
   ```

2. **Tesseract OCR**
   ```powershell
   # Install via Chocolatey
   choco install tesseract
   
   # Or download from: https://github.com/UB-Mannheim/tesseract/wiki
   # Add to PATH: C:\Program Files\Tesseract-OCR
   ```

3. **Install Python Packages**
   ```powershell
   cd D:\cos-ing-checker\cosing_checker
   pip install -r requirements.txt
   ```

---

## 🏃 Running the Application

### Terminal 1: Django Development Server
```powershell
cd D:\cos-ing-checker\cosing_checker
python manage.py runserver
```

### Terminal 2: Celery Worker
```powershell
cd D:\cos-ing-checker\cosing_checker
celery -A cosing_checker worker --loglevel=info --pool=solo
```
*Note: `--pool=solo` is required on Windows*

### Terminal 3: Redis Server (if not running as service)
```powershell
redis-server
```

---

## ✅ Testing the Features

### 1. **Test Redis Caching**
```powershell
# In Django shell
python manage.py shell

>>> from django.core.cache import cache
>>> cache.set('test_key', 'test_value', 300)
>>> cache.get('test_key')
'test_value'
```

### 2. **Test OCR Availability**
```powershell
python manage.py shell

>>> from analyzer.services.ocr import is_tesseract_available
>>> is_tesseract_available()
True  # Should return True if Tesseract installed
```

### 3. **Test Async Task**
```powershell
python manage.py shell

>>> from analyzer.tasks import run_analysis_task
>>> from analyzer.models import Analysis
>>> 
>>> # Create test analysis
>>> analysis = Analysis.objects.create(
...     input_text="Water, Glycerin",
...     input_source='text',
...     result_json={}
... )
>>> 
>>> # Trigger async task
>>> task = run_analysis_task.delay(analysis.id, "Water, Glycerin", 'text')
>>> task.id  # Task ID
>>> task.ready()  # Check if complete
>>> task.result  # Get result
```

### 4. **Run Tests**
```powershell
# Run OCR and async tests
python manage.py test analyzer.tests_ocr

# Run all tests
python manage.py test analyzer
```

### 5. **Test Image Upload (Browser)**
1. Navigate to http://localhost:8000/
2. Click on "📷 Image Upload" tab
3. Upload an image with ingredient text
4. Should show loading spinner, then results after processing

---

## 📊 Monitoring

### Check Celery Tasks
```powershell
# In Django shell
>>> from celery.result import AsyncResult
>>> result = AsyncResult('task-id-here')
>>> result.status  # PENDING, STARTED, SUCCESS, FAILURE
>>> result.result  # Task result
```

### Check Redis Keys
```powershell
redis-cli
> KEYS *
> GET cosing:prohibited_ingredients_list
> KEYS cosing:ingredient_check:*
```

### Clear Cache
```powershell
# In Django shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## 🎨 UI Features

### Text Input Tab
- Original comma-separated ingredient input
- Synchronous processing (immediate results)

### Image Upload Tab
- Upload JPG/PNG images of ingredient labels
- OCR extracts text automatically
- Async processing with loading indicator
- Auto-refresh when complete (polls every 2 seconds)

### Results Page
- Shows loading spinner for pending async tasks
- Displays "from OCR" label for image uploads
- Real-time status polling via AJAX

---

## 🔧 Troubleshooting

### Celery Worker Not Starting
```powershell
# Windows requires --pool=solo
celery -A cosing_checker worker --loglevel=info --pool=solo
```

### Redis Connection Error
```powershell
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Check Redis port
netstat -an | findstr :6379
```

### Tesseract Not Found
```powershell
# Add to PATH or set in settings.py:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Image Upload Fails
- Check MEDIA_ROOT directory exists
- Ensure proper file permissions
- Verify Tesseract installation: `tesseract --version`

---

## 📁 New Files Created

```
cosing_checker/
├── celery.py                       # Celery app configuration
├── analyzer/
│   ├── tasks.py                    # Async tasks (run_analysis_task, cleanup)
│   ├── tests_ocr.py                # OCR and async tests
│   └── services/
│       └── ocr.py                  # OCR service (enhanced)
└── media/                          # User uploads (auto-created)
    └── uploads/
```

---

## 🎯 Production Considerations

### For Production Deployment:
1. **Use production Redis instance**
   - AWS ElastiCache, Redis Cloud, or self-hosted
   - Update `CELERY_BROKER_URL` in settings

2. **Use production Celery worker manager**
   - Supervisor, systemd, or Docker
   - Multiple workers for scalability

3. **Configure proper media storage**
   - AWS S3, Azure Blob, or CDN
   - Update `DEFAULT_FILE_STORAGE` setting

4. **Add monitoring**
   - Flower for Celery monitoring
   - Sentry for error tracking
   - CloudWatch/Datadog for metrics

5. **Security**
   - Validate image uploads (size, format)
   - Rate limiting on OCR endpoint
   - HTTPS for all endpoints

---

## ✅ Day 3 Checklist Complete

- ✅ Celery + Redis setup
- ✅ Async task for analysis
- ✅ OCR pipeline with Tesseract
- ✅ Image upload handling
- ✅ Redis caching for ingredients
- ✅ Loading UI with polling
- ✅ Tests for OCR and async tasks
- ✅ Graceful error handling

**Next Steps**: Run the app, test image uploads, and verify async processing!
