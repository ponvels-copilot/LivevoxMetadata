"""Main processor for LivevoxMetadata processing system."""

import json
import time
from typing import List, Dict, Any, Optional, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging

from .config import Config
from .auth import JWTAuthenticator
from .s3_client import S3Client
from .api_client import APIClient
from .exceptions import LivevoxMetadataError, S3Error, APIError, BatchProcessingError
from .utils import setup_logging, is_peak_hour, safe_json_loads, get_timestamp


class MetadataProcessor:
    """Main processor for handling S3 files and API batch processing."""
    
    def __init__(self, config_file: Optional[str] = None, log_level: str = 'INFO'):
        """Initialize the metadata processor.
        
        Args:
            config_file: Optional path to .env configuration file
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # Set up logging
        self.logger = setup_logging(log_level)
        
        try:
            # Initialize configuration
            self.config = Config(config_file)
            self.logger.info("Configuration loaded successfully")
            
            # Initialize components
            self.authenticator = JWTAuthenticator(self.config)
            self.s3_client = S3Client(self.config)
            self.api_client = APIClient(self.config, self.authenticator)
            
            # Processing state
            self.stats = {
                'files_processed': 0,
                'records_processed': 0,
                'batches_sent': 0,
                'errors': 0,
                'start_time': None,
                'end_time': None
            }
            
            self.logger.info("MetadataProcessor initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MetadataProcessor: {e}")
            raise LivevoxMetadataError(f"Initialization failed: {e}")
    
    def parse_record(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single record line into a dictionary.
        
        Args:
            line: Raw line from the text file
            
        Returns:
            Parsed record dictionary or None if parsing fails
        """
        line = line.strip()
        if not line:
            return None
        
        # Try to parse as JSON first
        json_record = safe_json_loads(line)
        if json_record:
            return json_record
        
        # If not JSON, treat as delimited data (you can customize this)
        # For now, assume comma-separated values with basic structure
        try:
            parts = line.split(',')
            if len(parts) >= 2:
                return {
                    'id': parts[0].strip(),
                    'data': parts[1].strip(),
                    'additional_fields': parts[2:] if len(parts) > 2 else [],
                    'timestamp': get_timestamp(),
                    'source_line': line
                }
        except Exception as e:
            self.logger.warning(f"Failed to parse record line: {line[:100]}... Error: {e}")
        
        return None
    
    def process_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single file from S3.
        
        Args:
            file_info: File information dictionary from S3
            
        Returns:
            Processing results dictionary
        """
        s3_key = file_info['key']
        file_size = file_info['size']
        
        self.logger.info(f"Starting to process file: {s3_key} (size: {file_size} bytes)")
        
        start_time = time.time()
        records = []
        line_count = 0
        error_count = 0
        
        try:
            # Read file line by line for memory efficiency
            for line in self.s3_client.read_file_lines(s3_key):
                line_count += 1
                
                # Parse the line into a record
                record = self.parse_record(line)
                if record:
                    records.append(record)
                else:
                    error_count += 1
                    if error_count % 100 == 0:  # Log every 100 errors
                        self.logger.warning(f"Parse errors in {s3_key}: {error_count}/{line_count}")
                
                # Log progress for large files
                if line_count % 10000 == 0:
                    self.logger.info(f"Processed {line_count} lines from {s3_key}")
            
            # Send records to API in batches
            if records:
                self.logger.info(f"Sending {len(records)} records from {s3_key} to API")
                api_responses = self.api_client.process_records_in_batches(records)
                batch_count = len(api_responses)
            else:
                batch_count = 0
                api_responses = []
            
            processing_time = time.time() - start_time
            
            result = {
                'file': s3_key,
                'success': True,
                'lines_read': line_count,
                'records_parsed': len(records),
                'parse_errors': error_count,
                'batches_sent': batch_count,
                'processing_time': processing_time,
                'api_responses': api_responses
            }
            
            self.logger.info(
                f"Successfully processed {s3_key}: "
                f"{len(records)} records in {batch_count} batches "
                f"({processing_time:.2f}s)"
            )
            
            return result
            
        except S3Error as e:
            error_msg = f"S3 error processing {s3_key}: {e}"
            self.logger.error(error_msg)
            return {
                'file': s3_key,
                'success': False,
                'error': error_msg,
                'error_type': 'S3Error'
            }
            
        except APIError as e:
            error_msg = f"API error processing {s3_key}: {e}"
            self.logger.error(error_msg)
            return {
                'file': s3_key,
                'success': False,
                'error': error_msg,
                'error_type': 'APIError',
                'records_parsed': len(records)
            }
            
        except Exception as e:
            error_msg = f"Unexpected error processing {s3_key}: {e}"
            self.logger.error(error_msg)
            return {
                'file': s3_key,
                'success': False,
                'error': error_msg,
                'error_type': 'UnexpectedError'
            }
    
    def get_processing_parallelism(self) -> int:
        """Determine appropriate parallelism based on peak hours.
        
        Returns:
            Number of parallel workers to use
        """
        if is_peak_hour(
            self.config.timezone, 
            self.config.peak_start_hour, 
            self.config.peak_end_hour
        ):
            # Use full parallelism during peak hours
            workers = self.config.max_workers
            self.logger.info(f"Peak hours detected, using {workers} workers")
        else:
            # Use reduced parallelism during off-peak hours
            workers = max(1, self.config.max_workers // 2)
            self.logger.info(f"Off-peak hours, using {workers} workers")
        
        return workers
    
    def process_files(self, file_prefix: str = '', 
                     file_pattern: str = '.txt',
                     max_files: Optional[int] = None) -> Dict[str, Any]:
        """Process all matching files from S3.
        
        Args:
            file_prefix: S3 key prefix to filter files
            file_pattern: File pattern/extension to match
            max_files: Maximum number of files to process (for testing)
            
        Returns:
            Overall processing results
        """
        self.stats['start_time'] = datetime.utcnow()
        self.logger.info("Starting batch processing of S3 files")
        
        try:
            # Perform pre-processing health checks
            if not self.api_client.health_check():
                self.logger.warning("API health check failed, proceeding anyway")
            
            # List files to process
            files = self.s3_client.list_files(prefix=file_prefix, suffix=file_pattern)
            
            if not files:
                self.logger.warning(f"No files found with prefix '{file_prefix}' and pattern '{file_pattern}'")
                return self._build_final_results([])
            
            # Limit files for testing if specified
            if max_files and len(files) > max_files:
                files = files[:max_files]
                self.logger.info(f"Limited processing to {max_files} files")
            
            total_files = len(files)
            self.logger.info(f"Found {total_files} files to process")
            
            # Determine parallelism based on peak hours
            max_workers = self.get_processing_parallelism()
            
            results = []
            
            # Process files with thread pool for parallelism
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all file processing tasks
                future_to_file = {
                    executor.submit(self.process_file, file_info): file_info
                    for file_info in files
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_file):
                    file_info = future_to_file[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Update stats
                        if result['success']:
                            self.stats['files_processed'] += 1
                            self.stats['records_processed'] += result.get('records_parsed', 0)
                            self.stats['batches_sent'] += result.get('batches_sent', 0)
                        else:
                            self.stats['errors'] += 1
                        
                        # Log progress
                        completed = len(results)
                        if completed % 10 == 0 or completed == total_files:
                            self.logger.info(f"Progress: {completed}/{total_files} files processed")
                        
                    except Exception as e:
                        error_msg = f"Failed to process {file_info['key']}: {e}"
                        self.logger.error(error_msg)
                        results.append({
                            'file': file_info['key'],
                            'success': False,
                            'error': error_msg,
                            'error_type': 'ExecutorError'
                        })
                        self.stats['errors'] += 1
            
            return self._build_final_results(results)
            
        except Exception as e:
            self.logger.error(f"Critical error in process_files: {e}")
            raise BatchProcessingError(f"Batch processing failed: {e}")
        finally:
            self.stats['end_time'] = datetime.utcnow()
    
    def _build_final_results(self, file_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build final processing results summary.
        
        Args:
            file_results: List of individual file processing results
            
        Returns:
            Summary results dictionary
        """
        successful_files = [r for r in file_results if r['success']]
        failed_files = [r for r in file_results if not r['success']]
        
        processing_duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            processing_duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        summary = {
            'overall_success': len(failed_files) == 0,
            'total_files': len(file_results),
            'successful_files': len(successful_files),
            'failed_files': len(failed_files),
            'total_records_processed': self.stats['records_processed'],
            'total_batches_sent': self.stats['batches_sent'],
            'processing_duration_seconds': processing_duration,
            'start_time': self.stats['start_time'].isoformat() if self.stats['start_time'] else None,
            'end_time': self.stats['end_time'].isoformat() if self.stats['end_time'] else None,
            'file_results': file_results
        }
        
        # Log final summary
        self.logger.info(
            f"Processing complete: {len(successful_files)}/{len(file_results)} files successful, "
            f"{self.stats['records_processed']} total records processed"
        )
        
        if failed_files:
            self.logger.error(f"Failed files: {[f['file'] for f in failed_files]}")
        
        return summary