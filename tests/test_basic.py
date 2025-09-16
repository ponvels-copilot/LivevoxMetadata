"""Test configuration and basic functionality."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
import boto3
from moto import mock_aws

from src.livevox_metadata.config import Config, ConfigurationError
from src.livevox_metadata.auth import JWTAuthenticator
from src.livevox_metadata.s3_client import S3Client
from src.livevox_metadata.utils import chunk_list, is_peak_hour, exponential_backoff


class TestConfig(unittest.TestCase):
    """Test configuration management."""
    
    def setUp(self):
        # Create temporary env file
        self.temp_env = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env')
        self.temp_env.write("""
AWS_ACCESS_KEY_ID=test_access_key
AWS_SECRET_ACCESS_KEY=test_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=test-bucket
API_BASE_URL=https://api.example.com
JWT_SECRET_KEY=test_secret
MAX_BATCH_SIZE=250
""")
        self.temp_env.close()
    
    def tearDown(self):
        os.unlink(self.temp_env.name)
    
    def test_config_loading(self):
        """Test configuration loading from env file."""
        config = Config(self.temp_env.name)
        
        self.assertEqual(config.aws_access_key_id, 'test_access_key')
        self.assertEqual(config.s3_bucket_name, 'test-bucket')
        self.assertEqual(config.max_batch_size, 250)
    
    def test_missing_required_config(self):
        """Test error handling for missing required configuration."""
        # Create env file missing required variables
        temp_env = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env')
        temp_env.write("AWS_ACCESS_KEY_ID=test_key\n")
        temp_env.close()
        
        try:
            with self.assertRaises(ConfigurationError):
                Config(temp_env.name)
        finally:
            os.unlink(temp_env.name)


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def test_chunk_list(self):
        """Test list chunking functionality."""
        items = list(range(10))
        chunks = list(chunk_list(items, 3))
        
        expected = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
        self.assertEqual(chunks, expected)
    
    def test_chunk_list_empty(self):
        """Test chunking empty list."""
        items = []
        chunks = list(chunk_list(items, 3))
        self.assertEqual(chunks, [])
    
    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        delay1 = exponential_backoff(0, base_delay=1.0, factor=2.0)
        delay2 = exponential_backoff(1, base_delay=1.0, factor=2.0)
        delay3 = exponential_backoff(2, base_delay=1.0, factor=2.0)
        
        self.assertEqual(delay1, 1.0)
        self.assertEqual(delay2, 2.0)
        self.assertEqual(delay3, 4.0)


class TestJWTAuth(unittest.TestCase):
    """Test JWT authentication."""
    
    def setUp(self):
        # Create test config
        temp_env = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env')
        temp_env.write("""
AWS_ACCESS_KEY_ID=test_access_key
AWS_SECRET_ACCESS_KEY=test_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=test-bucket
API_BASE_URL=https://api.example.com
JWT_SECRET_KEY=test_secret_key_123
""")
        temp_env.close()
        
        self.config = Config(temp_env.name)
        self.authenticator = JWTAuthenticator(self.config)
        
        # Cleanup
        os.unlink(temp_env.name)
    
    def test_generate_token(self):
        """Test JWT token generation."""
        token = self.authenticator.generate_token()
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
    
    def test_validate_token(self):
        """Test JWT token validation."""
        token = self.authenticator.generate_token({'user': 'test'})
        payload = self.authenticator.validate_token(token)
        
        self.assertEqual(payload['user'], 'test')
        self.assertEqual(payload['sub'], 'data-processing')
    
    def test_get_auth_headers(self):
        """Test authorization headers generation."""
        headers = self.authenticator.get_auth_headers()
        
        self.assertIn('Authorization', headers)
        self.assertTrue(headers['Authorization'].startswith('Bearer '))


@mock_aws
class TestS3Client(unittest.TestCase):
    """Test S3 client functionality."""
    
    def setUp(self):
        # Create test config
        temp_env = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env')
        temp_env.write("""
AWS_ACCESS_KEY_ID=test_access_key
AWS_SECRET_ACCESS_KEY=test_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=test-bucket
API_BASE_URL=https://api.example.com
JWT_SECRET_KEY=test_secret_key
""")
        temp_env.close()
        
        self.config = Config(temp_env.name)
        
        # Create mock S3 bucket and objects
        self.s3 = boto3.client('s3', region_name='us-east-1')
        self.s3.create_bucket(Bucket='test-bucket')
        
        # Upload test files
        self.s3.put_object(Bucket='test-bucket', Key='test1.txt', Body=b'line1\nline2\nline3')
        self.s3.put_object(Bucket='test-bucket', Key='test2.txt', Body=b'{"id": "1", "data": "test"}')
        
        self.s3_client = S3Client(self.config)
        
        # Cleanup
        os.unlink(temp_env.name)
    
    def test_list_files(self):
        """Test S3 file listing."""
        files = self.s3_client.list_files()
        
        self.assertEqual(len(files), 2)
        file_keys = [f['key'] for f in files]
        self.assertIn('test1.txt', file_keys)
        self.assertIn('test2.txt', file_keys)
    
    def test_read_file_content(self):
        """Test reading file content."""
        content = self.s3_client.read_file_content('test1.txt')
        self.assertEqual(content, 'line1\nline2\nline3')
    
    def test_read_file_lines(self):
        """Test reading file lines."""
        lines = list(self.s3_client.read_file_lines('test1.txt'))
        self.assertEqual(lines, ['line1', 'line2', 'line3'])
    
    def test_file_exists(self):
        """Test file existence check."""
        self.assertTrue(self.s3_client.file_exists('test1.txt'))
        self.assertFalse(self.s3_client.file_exists('nonexistent.txt'))


if __name__ == '__main__':
    unittest.main()