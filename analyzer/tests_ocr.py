"""
Tests for OCR functionality and async task processing.
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
from PIL import Image
from io import BytesIO

from analyzer.services.ocr import extract_text_from_image, OCRError, is_tesseract_available
from analyzer.tasks import run_analysis_task
from analyzer.models import Analysis


class OCRServiceTests(TestCase):
    """Test OCR service functionality"""
    
    def create_test_image(self):
        """Helper to create a test image"""
        img = Image.new('RGB', (100, 100), color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return buffer
    
    @patch('analyzer.services.ocr.pytesseract.image_to_string')
    def test_extract_text_success(self, mock_ocr):
        """Test successful text extraction"""
        mock_ocr.return_value = "Aqua, Glycerin, Sodium Laureth Sulfate"
        
        test_image = self.create_test_image()
        result = extract_text_from_image(test_image)
        
        self.assertEqual(result, "Aqua, Glycerin, Sodium Laureth Sulfate")
        mock_ocr.assert_called_once()
    
    @patch('analyzer.services.ocr.pytesseract.image_to_string')
    def test_extract_text_empty(self, mock_ocr):
        """Test OCR with no text found"""
        mock_ocr.return_value = ""
        
        test_image = self.create_test_image()
        result = extract_text_from_image(test_image)
        
        self.assertEqual(result, "")
    
    @patch('analyzer.services.ocr.pytesseract.image_to_string')
    def test_extract_text_tesseract_not_found(self, mock_ocr):
        """Test behavior when Tesseract is not installed"""
        from pytesseract import TesseractNotFoundError
        mock_ocr.side_effect = TesseractNotFoundError()
        
        test_image = self.create_test_image()
        
        with self.assertRaises(OCRError) as cm:
            extract_text_from_image(test_image)
        
        self.assertIn("OCR engine not available", str(cm.exception))
    
    @patch('analyzer.services.ocr.pytesseract.get_tesseract_version')
    def test_is_tesseract_available_true(self, mock_version):
        """Test Tesseract availability check when available"""
        mock_version.return_value = "5.0.0"
        
        self.assertTrue(is_tesseract_available())
    
    @patch('analyzer.services.ocr.pytesseract.get_tesseract_version')
    def test_is_tesseract_available_false(self, mock_version):
        """Test Tesseract availability check when not available"""
        from pytesseract import TesseractNotFoundError
        mock_version.side_effect = TesseractNotFoundError()
        
        self.assertFalse(is_tesseract_available())


class AsyncTaskTests(TestCase):
    """Test async task processing"""
    
    def setUp(self):
        """Set up test data"""
        # Load test data
        from analyzer.management.commands.load_annex_ii import Command
        from io import StringIO
        import os
        
        csv_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'datasets', 'COSING_Annex_II_v2.csv'
        )
        if os.path.exists(csv_path):
            cmd = Command()
            cmd.handle(csv_file=csv_path, verbosity=0, stdout=StringIO())
    
    @patch('analyzer.tasks.logger')
    def test_run_analysis_task_success(self, mock_logger):
        """Test successful async analysis task"""
        # Create an analysis record
        analysis = Analysis.objects.create(
            input_text="Water, Glycerin, Phenoxyethanol",
            input_source='text',
            result_json={},
            overall_status='safe'
        )
        
        # Run the task (sync for testing)
        result = run_analysis_task(
            analysis.id,
            "Water, Glycerin, Phenoxyethanol",
            'text'
        )
        
        # Refresh from database
        analysis.refresh_from_db()
        
        # Assertions
        self.assertEqual(result['status'], 'completed')
        self.assertIsNotNone(analysis.result_json)
        self.assertIn('results', analysis.result_json)
        self.assertGreater(analysis.total_ingredients, 0)
        self.assertGreater(analysis.analysis_duration_ms, 0)
    
    @patch('analyzer.tasks.logger')
    def test_run_analysis_task_with_prohibited(self, mock_logger):
        """Test async task with prohibited ingredients"""
        # Create an analysis record
        analysis = Analysis.objects.create(
            input_text="Water, Formaldehyde, Glycerin",
            input_source='text',
            result_json={},
            overall_status='safe'
        )
        
        # Run the task
        result = run_analysis_task(
            analysis.id,
            "Water, Formaldehyde, Glycerin",
            'text'
        )
        
        # Refresh from database
        analysis.refresh_from_db()
        
        # Assertions
        self.assertEqual(result['overall_status'], 'prohibited')
        self.assertEqual(analysis.overall_status, 'prohibited')
        self.assertGreater(analysis.prohibited_count, 0)
    
    def test_run_analysis_task_not_found(self):
        """Test task with non-existent analysis ID"""
        with self.assertRaises(Analysis.DoesNotExist):
            run_analysis_task(9999, "Water, Glycerin", 'text')


class OCRIntegrationTests(TestCase):
    """Integration tests for OCR + async workflow"""
    
    @patch('analyzer.views.is_tesseract_available')
    @patch('analyzer.views.extract_text_from_image')
    @patch('analyzer.views.run_analysis_task.delay')
    def test_image_upload_workflow(self, mock_task, mock_ocr, mock_available):
        """Test complete image upload to async processing workflow"""
        # Mock OCR availability and extraction
        mock_available.return_value = True
        mock_ocr.return_value = "Aqua, Glycerin"
        
        # Mock Celery task
        mock_task.return_value = MagicMock(id='test-task-id')
        
        # Create test image upload
        img = Image.new('RGB', (100, 100), color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            "test_ingredients.png",
            buffer.getvalue(),
            content_type="image/png"
        )
        
        # Submit form with image
        response = self.client.post('/', {
            'image_file': uploaded_file
        })
        
        # Should redirect to results page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/analysis/', response.url)
        
        # Verify task was triggered
        mock_task.assert_called_once()
        
        # Verify Analysis record was created
        analysis = Analysis.objects.latest('created_at')
        self.assertEqual(analysis.input_source, 'image')
        self.assertEqual(analysis.input_text, "Aqua, Glycerin")
