"""S3 client for reading text files in LivevoxMetadata processing."""

import boto3
import io
import time
from typing import Iterator, List, Optional, Dict, Any
from botocore.exceptions import ClientError, BotoCoreError
import logging

from .config import Config
from .exceptions import S3Error
from .utils import exponential_backoff, format_file_size


class S3Client:
    """S3 client for reading text files and processing records."""
    
    def __init__(self, config: Config):
        """Initialize S3 client.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.aws_access_key_id,
                aws_secret_access_key=config.aws_secret_access_key,
                region_name=config.aws_region
            )
            self.logger.info(f"Initialized S3 client for region {config.aws_region}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")
            raise S3Error(f"S3 client initialization failed: {e}")
    
    def list_files(self, prefix: str = '', suffix: str = '.txt') -> List[Dict[str, Any]]:
        """List files in S3 bucket with optional filtering.
        
        Args:
            prefix: Optional prefix to filter files
            suffix: File extension filter (default: .txt)
            
        Returns:
            List of file information dictionaries
            
        Raises:
            S3Error: If listing files fails
        """
        try:
            files = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            page_iterator = paginator.paginate(
                Bucket=self.config.s3_bucket_name,
                Prefix=prefix
            )
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['Key'].endswith(suffix):
                            files.append({
                                'key': obj['Key'],
                                'size': obj['Size'],
                                'last_modified': obj['LastModified'],
                                'etag': obj['ETag']
                            })
            
            self.logger.info(f"Found {len(files)} files in S3 bucket")
            return files
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self.logger.error(f"S3 ClientError listing files: {error_code} - {e}")
            raise S3Error(f"Failed to list S3 files: {error_code}")
        except Exception as e:
            self.logger.error(f"Unexpected error listing S3 files: {e}")
            raise S3Error(f"Failed to list S3 files: {e}")
    
    def read_file_content(self, s3_key: str, encoding: str = 'utf-8') -> str:
        """Read complete content of an S3 file.
        
        Args:
            s3_key: S3 object key
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string
            
        Raises:
            S3Error: If reading file fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.s3_bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read().decode(encoding)
            file_size = response['ContentLength']
            
            self.logger.debug(
                f"Read file {s3_key}, size: {format_file_size(file_size)}"
            )
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self.logger.error(f"S3 ClientError reading file {s3_key}: {error_code} - {e}")
            raise S3Error(f"Failed to read S3 file {s3_key}: {error_code}")
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error reading file {s3_key}: {e}")
            raise S3Error(f"Failed to decode file {s3_key} with encoding {encoding}")
        except Exception as e:
            self.logger.error(f"Unexpected error reading file {s3_key}: {e}")
            raise S3Error(f"Failed to read S3 file {s3_key}: {e}")
    
    def read_file_lines(self, s3_key: str, encoding: str = 'utf-8',
                       skip_empty: bool = True) -> Iterator[str]:
        """Read file content line by line as iterator.
        
        Args:
            s3_key: S3 object key
            encoding: File encoding (default: utf-8)
            skip_empty: Skip empty lines if True
            
        Yields:
            Individual lines from the file
            
        Raises:
            S3Error: If reading file fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.s3_bucket_name,
                Key=s3_key
            )
            
            # Stream the file content line by line to handle large files efficiently
            stream = response['Body']
            for line in stream.iter_lines(chunk_size=8192):
                decoded_line = line.decode(encoding).strip()
                if not skip_empty or decoded_line:
                    yield decoded_line
                    
        except ClientError as e:
            error_code = e.response['Error']['Code']
            self.logger.error(f"S3 ClientError reading file {s3_key}: {error_code} - {e}")
            raise S3Error(f"Failed to read S3 file {s3_key}: {error_code}")
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error reading file {s3_key}: {e}")
            raise S3Error(f"Failed to decode file {s3_key} with encoding {encoding}")
        except Exception as e:
            self.logger.error(f"Unexpected error reading file {s3_key}: {e}")
            raise S3Error(f"Failed to read S3 file {s3_key}: {e}")
    
    def read_file_with_retry(self, s3_key: str, encoding: str = 'utf-8',
                           max_retries: Optional[int] = None) -> str:
        """Read file with retry logic for improved reliability.
        
        Args:
            s3_key: S3 object key
            encoding: File encoding
            max_retries: Maximum number of retry attempts
            
        Returns:
            File content as string
            
        Raises:
            S3Error: If all retry attempts fail
        """
        if max_retries is None:
            max_retries = self.config.max_retries
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.read_file_content(s3_key, encoding)
                
            except S3Error as e:
                last_error = e
                if attempt < max_retries:
                    delay = exponential_backoff(attempt, factor=self.config.retry_backoff_factor)
                    self.logger.warning(
                        f"Read attempt {attempt + 1} failed for {s3_key}, "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"All read attempts failed for {s3_key}: {e}")
        
        raise S3Error(f"Failed to read {s3_key} after {max_retries} attempts: {last_error}")
    
    def file_exists(self, s3_key: str) -> bool:
        """Check if a file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.config.s3_bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                self.logger.warning(f"Error checking file existence for {s3_key}: {e}")
                return False
        except Exception as e:
            self.logger.warning(f"Unexpected error checking file existence for {s3_key}: {e}")
            return False
    
    def get_file_info(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata information for an S3 file.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            File metadata dictionary or None if file doesn't exist
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.config.s3_bucket_name,
                Key=s3_key
            )
            
            return {
                'key': s3_key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'],
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            else:
                self.logger.warning(f"Error getting file info for {s3_key}: {e}")
                return None
        except Exception as e:
            self.logger.warning(f"Unexpected error getting file info for {s3_key}: {e}")
            return None