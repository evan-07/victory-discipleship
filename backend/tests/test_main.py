#!/usr/bin/env python3
"""
Tests for the /api/submit endpoint.
"""

import pytest
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json
import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock BigQuery client before importing main
with patch('google.cloud.bigquery.Client'):
    from main import app


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_submit_form_valid_payload(client):
    """Test successful form submission with valid data"""
    with patch('main.client.insert_rows_json') as mock_insert:
        mock_insert.return_value = []  # No errors from BigQuery
        
        response = client.post('/api/submit', json={
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
            "primaryMobile": "123456789"
        })
        
        assert response.status_code == 200
        assert response.json['result'] == 'success'
        mock_insert.assert_called_once()


def test_submit_form_honeypot_spam_detection(client):
    """Test honeypot field detects and silently rejects spam"""
    with patch('main.client.insert_rows_json') as mock_insert:
        response = client.post('/api/submit', json={
            "firstName": "Spammer",
            "lastName": "Bot",
            "email": "spam@bot.com",
            "website_url": "http://spam-site.com"  # Honeypot field
        })
        
        # Should return success to fool bot, but not insert
        assert response.status_code == 200
        assert response.json['result'] == 'success'
        mock_insert.assert_not_called()


def test_submit_form_empty_payload(client):
    """Test rejection of empty payload"""
    response = client.post('/api/submit', json={})
    
    assert response.status_code == 400
    assert response.json['result'] == 'error'
    assert 'Empty payload' in response.json['message']


def test_submit_form_non_json_request(client):
    """Test rejection of non-JSON content type"""
    response = client.post('/api/submit', 
                          data="not json content",
                          content_type='text/plain')
    
    assert response.status_code == 400
    assert response.json['result'] == 'error'
    assert 'must be JSON' in response.json['message']


def test_submit_form_bigquery_error(client):
    """Test handling of BigQuery insertion errors"""
    with patch('main.client.insert_rows_json') as mock_insert:
        mock_insert.return_value = [{'errors': ['Database error']}]
        
        response = client.post('/api/submit', json={
            "firstName": "Jane",
            "lastName": "Smith",
            "email": "jane@example.com"
        })
        
        assert response.status_code == 500
        assert response.json['result'] == 'error'
        assert 'Database error' in response.json['message']


def test_submit_form_includes_metadata(client):
    """Test that submission includes IP and user agent metadata"""
    with patch('main.client.insert_rows_json') as mock_insert:
        mock_insert.return_value = []
        
        response = client.post('/api/submit',
                               json={"firstName": "Test", "lastName": "User", "email": "test@example.com"},
                               headers={'X-Forwarded-For': '1.2.3.4', 'User-Agent': 'TestBrowser/1.0'})
        
        assert response.status_code == 200
        # Verify metadata was captured (check mock call args)
        call_args = mock_insert.call_args[0][1][0]
        assert 'metadata' in call_args


def test_submit_form(client):
    """Base test for submit_form function - validates basic functionality"""
    with patch('main.client.insert_rows_json') as mock_insert:
        mock_insert.return_value = []
        response = client.post('/api/submit', json={"firstName": "Test", "lastName": "User", "email": "test@example.com"})
        assert response.status_code == 200


def test_search_members(client):
    """Base test for search_members function - validates basic functionality"""
    with patch('main.client.query') as mock_query:
        mock_result = MagicMock()
        mock_result.result.return_value = []
        mock_query.return_value = mock_result
        response = client.get('/api/search?query=test@example.com')
        assert response.status_code == 200


def test_search_members_by_exact_email(client):
    """Test search by exact email match"""
    with patch('main.client.query') as mock_query:
        # Mock BigQuery result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.items.return_value = [
            ('email', 'john@example.com'),
            ('first_name', 'John'),
            ('last_name', 'Doe'),
            ('mobile_number', '09123456789')
        ]
        mock_result.result.return_value = [mock_row]
        mock_query.return_value = mock_result
        
        response = client.get('/api/search?query=john@example.com')
        
        assert response.status_code == 200
        assert response.json['result'] == 'success'
        assert len(response.json['members']) == 1
        assert response.json['members'][0]['email'] == 'john@example.com'


def test_search_members_by_partial_name(client):
    """Test search by partial first or last name"""
    with patch('main.client.query') as mock_query:
        mock_result = MagicMock()
        mock_row1 = MagicMock()
        mock_row1.items.return_value = [('first_name', 'John'), ('last_name', 'Doe'), ('email', 'john@example.com')]
        mock_row2 = MagicMock()
        mock_row2.items.return_value = [('first_name', 'Johnny'), ('last_name', 'Smith'), ('email', 'johnny@example.com')]
        mock_result.result.return_value = [mock_row1, mock_row2]
        mock_query.return_value = mock_result
        
        response = client.get('/api/search?query=john')
        
        assert response.status_code == 200
        assert response.json['result'] == 'success'
        assert len(response.json['members']) == 2


def test_search_members_empty_query_parameter(client):
    """Test rejection of empty query parameter"""
    response = client.get('/api/search?query=')
    
    assert response.status_code == 400
    assert response.json['result'] == 'error'
    assert 'Query parameter required' in response.json['message']


def test_search_members_bigquery_error(client):
    """Test handling of BigQuery query errors"""
    with patch('main.client.query') as mock_query:
        mock_query.side_effect = Exception("BigQuery connection failed")
        
        response = client.get('/api/search?query=test@example.com')
        
        assert response.status_code == 500
        assert response.json['result'] == 'error'
        assert 'Search failed' in response.json['message']


def test_get_api_version(client):
    """Test get_api_version function returns correct version"""
    from main import get_api_version
    
    version = get_api_version()
    
    assert version == "1.0.0"
    assert isinstance(version, str)


def test_get_reference_data(client):
    """Test /api/reference-data endpoint"""
    with patch('main.client.query') as mock_query:
        # Mock BigQuery result
        mock_result = MagicMock()
        mock_row1 = MagicMock()
        mock_row1.__getitem__ = lambda self, key: {
            'category': 'discipleship_classes',
            'value': 'ONE 2 ONE',
            'display_order': 1
        }[key]
        mock_row2 = MagicMock()
        mock_row2.__getitem__ = lambda self, key: {
            'category': 'discipleship_classes',
            'value': 'Victory Weekend',
            'display_order': 2
        }[key]
        mock_row3 = MagicMock()
        mock_row3.__getitem__ = lambda self, key: {
            'category': 'ministry_teams',
            'value': 'Kids Ministry',
            'display_order': 1
        }[key]
        
        mock_result.result.return_value = [mock_row1, mock_row2, mock_row3]
        mock_query.return_value = mock_result
        
        response = client.get('/api/reference-data')
        
        assert response.status_code == 200
        assert response.json['result'] == 'success'
        assert 'data' in response.json
        assert 'discipleship_classes' in response.json['data']
        assert 'ministry_teams' in response.json['data']
        assert len(response.json['data']['discipleship_classes']) == 2
        assert len(response.json['data']['ministry_teams']) == 1


def test_get_reference_data_error(client):
    """Test /api/reference-data handles BigQuery errors gracefully"""
    with patch('main.client.query') as mock_query:
        mock_query.side_effect = Exception("BigQuery connection failed")
        
        response = client.get('/api/reference-data')
        
        assert response.status_code == 500
        assert response.json['result'] == 'error'
        assert 'Failed to fetch reference data' in response.json['message']
