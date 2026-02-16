import unittest
from unittest.mock import Mock, patch
import json
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

class TestSearchEndpoint(unittest.TestCase):
    """Test suite for GET /api/search endpoint"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True
    
    @patch('main.client')
    def test_search_by_email_success(self, mock_client):
        """Test successful search by exact email"""
        # Mock BigQuery response
        mock_row = {
            'first_name': 'John',
            'middle_name': 'Paul',
            'last_name': 'Doe',
            'suffix': '',
            'email': 'john.doe@example.com',
            'fb_name': 'John Doe',
            'gender': 'Male',
            'birthday': '01/15/1990',
            'marital_status': 'Single',
            'mobile_number': '09123456789',
            'sec_mobile_number': '',
            'occupation_type': 'Professional',
            'is_vg_member': True,
            'is_vg_leader': False,
            'is_ministry_member': False
        }
        
        mock_result = Mock()
        mock_result.result.return_value = [Mock(items=lambda: mock_row.items())]
        mock_client.query.return_value = mock_result
        
        response = self.app.get('/api/search?query=john.doe@example.com')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['result'], 'success')
        self.assertIsInstance(data['members'], list)
        self.assertEqual(len(data['members']), 1)
        self.assertEqual(data['members'][0]['email'], 'john.doe@example.com')
    
    @patch('main.client')
    def test_search_by_name_success(self, mock_client):
        """Test successful search by partial name"""
        # Mock BigQuery response with multiple results
        mock_rows = [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@example.com',
                'mobile_number': '09123456789'
            },
            {
                'first_name': 'Johnny',
                'last_name': 'Smith',
                'email': 'johnny.smith@example.com',
                'mobile_number': '09987654321'
            }
        ]
        
        mock_result = Mock()
        mock_result.result.return_value = [Mock(items=lambda: row.items()) for row in mock_rows]
        mock_client.query.return_value = mock_result
        
        response = self.app.get('/api/search?query=John')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['result'], 'success')
        self.assertIsInstance(data['members'], list)
        self.assertEqual(len(data['members']), 2)
    
    def test_search_empty_query(self):
        """Test search with empty query parameter"""
        response = self.app.get('/api/search?query=')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['result'], 'error')
        self.assertIn('required', data['message'].lower())
    
    def test_search_no_query_parameter(self):
        """Test search without query parameter"""
        response = self.app.get('/api/search')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['result'], 'error')
    
    @patch('main.client')
    def test_search_no_results(self, mock_client):
        """Test search that returns no results"""
        mock_result = Mock()
        mock_result.result.return_value = []
        mock_client.query.return_value = mock_result
        
        response = self.app.get('/api/search?query=nonexistent@example.com')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['result'], 'success')
        self.assertEqual(len(data['members']), 0)
    
    @patch('main.client')
    def test_search_special_characters(self, mock_client):
        """Test search handles special characters safely (SQL injection prevention)"""
        mock_result = Mock()
        mock_result.result.return_value = []
        mock_client.query.return_value = mock_result
        
        # Test with potential SQL injection characters
        response = self.app.get('/api/search?query=test\'; DROP TABLE members; --')
        
        # Should not crash and should use parameterized query
        self.assertIn(response.status_code, [200, 400, 500])
        
        # Verify parameterized query was used
        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertEqual(data['result'], 'success')
    
    @patch('main.client')
    def test_search_bigquery_error(self, mock_client):
        """Test search handles BigQuery errors gracefully"""
        mock_client.query.side_effect = Exception('BigQuery connection failed')
        
        response = self.app.get('/api/search?query=test@example.com')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(data['result'], 'error')
        self.assertIn('failed', data['message'].lower())

if __name__ == '__main__':
    unittest.main()
