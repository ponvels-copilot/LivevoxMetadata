"""Configuration management for LivevoxMetadata processing."""

import os
from typing import Optional
from dotenv import load_dotenv

from .exceptions import ConfigurationError


class Config:
    """Configuration manager for the LivevoxMetadata processing system."""
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            env_file: Optional path to .env file. If None, looks for .env in current directory.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        self._validate_required_config()
    
    def _validate_required_config(self) -> None:
        """Validate that required configuration values are present."""
        required_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY', 
            'AWS_REGION',
            'S3_BUCKET_NAME',
            'API_BASE_URL',
            'JWT_SECRET_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ConfigurationError(
                f"Missing required configuration variables: {', '.join(missing_vars)}"
            )
    
    @property
    def aws_access_key_id(self) -> str:
        """AWS access key ID."""
        return os.getenv('AWS_ACCESS_KEY_ID', '')
    
    @property
    def aws_secret_access_key(self) -> str:
        """AWS secret access key."""
        return os.getenv('AWS_SECRET_ACCESS_KEY', '')
    
    @property
    def aws_region(self) -> str:
        """AWS region."""
        return os.getenv('AWS_REGION', 'us-east-1')
    
    @property
    def s3_bucket_name(self) -> str:
        """S3 bucket name."""
        return os.getenv('S3_BUCKET_NAME', '')
    
    @property
    def api_base_url(self) -> str:
        """API base URL."""
        return os.getenv('API_BASE_URL', '')
    
    @property
    def jwt_secret_key(self) -> str:
        """JWT secret key."""
        return os.getenv('JWT_SECRET_KEY', '')
    
    @property
    def jwt_algorithm(self) -> str:
        """JWT algorithm."""
        return os.getenv('JWT_ALGORITHM', 'HS256')
    
    @property
    def max_batch_size(self) -> int:
        """Maximum batch size for API requests."""
        return int(os.getenv('MAX_BATCH_SIZE', '500'))
    
    @property
    def max_workers(self) -> int:
        """Maximum number of worker threads."""
        return int(os.getenv('MAX_WORKERS', '10'))
    
    @property
    def peak_start_hour(self) -> int:
        """Peak processing start hour (24-hour format)."""
        return int(os.getenv('PEAK_START_HOUR', '10'))
    
    @property
    def peak_end_hour(self) -> int:
        """Peak processing end hour (24-hour format)."""
        return int(os.getenv('PEAK_END_HOUR', '20'))
    
    @property
    def timezone(self) -> str:
        """Timezone for peak hour calculations."""
        return os.getenv('TIMEZONE', 'America/New_York')
    
    @property
    def max_retries(self) -> int:
        """Maximum number of retries for failed operations."""
        return int(os.getenv('MAX_RETRIES', '3'))
    
    @property
    def retry_backoff_factor(self) -> float:
        """Backoff factor for retries."""
        return float(os.getenv('RETRY_BACKOFF_FACTOR', '2.0'))