#!/usr/bin/env python3
"""
Tests for the /api/search endpoint (comprehensive).
"""
import pytest
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json

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


def test_search_members_no_results(client):
    """Test search returning no results"""
    with patch('main.client.query') as mock_query:
        mock_result = MagicMock()
        mock_result.result.return_value = []
        mock_query.return_value = mock_result
        
        response = client.get('/api/search?query=nonexistent@example.com')
        
        assert response.status_code == 200
        assert response.json['result'] == 'success'
        assert len(response.json['members']) == 0


def test_search_members_empty_query_parameter(client):
    """Test rejection of empty query parameter"""
    response = client.get('/api/search?query=')
    
    assert response.status_code == 400
    assert response.json['result'] == 'error'
    assert 'Query parameter required' in response.json['message']


def test_search_members_missing_query_parameter(client):
    """Test rejection when query parameter is missing"""
    response = client.get('/api/search')
    
    assert response.status_code == 400
    assert response.json['result'] == 'error'


def test_search_members_bigquery_error(client):
    """Test handling of BigQuery query errors"""
    with patch('main.client.query') as mock_query:
        mock_query.side_effect = Exception("BigQuery connection failed")
        
        response = client.get('/api/search?query=test@example.com')
        
        assert response.status_code == 500
        assert response.json['result'] == 'error'
        assert 'Search failed' in response.json['message']


def test_search_members_uses_parameterized_query(client):
    """Test that search uses parameterized queries (SQL injection protection)"""
    with patch('main.client.query') as mock_query:
        mock_result = MagicMock()
        mock_result.result.return_value = []
        mock_query.return_value = mock_result
        
        # Attempt SQL injection
        response = client.get('/api/search?query=test@example.com\' OR 1=1--')
        
        # Should still execute safely with parameterized query
        assert response.status_code == 200
        # Verify QueryJobConfig was used (parameterized query)
        mock_query.assert_called_once()
        call_args = mock_query.call_args
        assert call_args[1]['job_config'] is not None
