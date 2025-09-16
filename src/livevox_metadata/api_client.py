"""API client for batch processing in LivevoxMetadata processing."""

import requests
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

from .config import Config
from .auth import JWTAuthenticator
from .exceptions import APIError, AuthenticationError
from .utils import exponential_backoff, chunk_list, get_timestamp


class APIClient:
    """API client for sending batched records to endpoints."""
    
    def __init__(self, config: Config, authenticator: JWTAuthenticator):
        """Initialize API client.
        
        Args:
            config: Configuration instance
            authenticator: JWT authenticator instance
        """
        self.config = config
        self.authenticator = authenticator
        self.logger = logging.getLogger(__name__)
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=config.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.logger.info(f"Initialized API client for {config.api_base_url}")
    
    def send_batch(self, records: List[Dict[str, Any]], 
                   endpoint: str = "/api/records",
                   timeout: int = 30) -> Dict[str, Any]:
        """Send a batch of records to the API endpoint.
        
        Args:
            records: List of record dictionaries to send
            endpoint: API endpoint path
            timeout: Request timeout in seconds
            
        Returns:
            API response data
            
        Raises:
            APIError: If API request fails
            AuthenticationError: If authentication fails
        """
        if not records:
            raise APIError("Cannot send empty batch")
        
        if len(records) > self.config.max_batch_size:
            raise APIError(f"Batch size {len(records)} exceeds maximum {self.config.max_batch_size}")
        
        url = f"{self.config.api_base_url.rstrip('/')}{endpoint}"
        
        # Prepare batch payload
        payload = {
            "records": records,
            "batch_size": len(records),
            "timestamp": get_timestamp(),
            "source": "livevox-metadata-processor"
        }
        
        try:
            # Get authentication headers
            headers = self.authenticator.get_auth_headers()
            
            self.logger.debug(f"Sending batch of {len(records)} records to {url}")
            
            response = self.session.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            self.logger.info(f"Successfully sent batch of {len(records)} records")
            return response_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.logger.warning("Authentication failed, attempting token refresh")
                raise AuthenticationError(f"Authentication failed: {e}")
            else:
                error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
                self.logger.error(error_msg)
                raise APIError(error_msg)
                
        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout after {timeout}s"
            self.logger.error(error_msg)
            raise APIError(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {e}"
            self.logger.error(error_msg)
            raise APIError(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {e}"
            self.logger.error(error_msg)
            raise APIError(error_msg)
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {e}"
            self.logger.error(error_msg)
            raise APIError(error_msg)
    
    def send_batch_with_retry(self, records: List[Dict[str, Any]], 
                             endpoint: str = "/api/records",
                             timeout: int = 30,
                             max_retries: Optional[int] = None) -> Dict[str, Any]:
        """Send batch with retry logic and authentication refresh.
        
        Args:
            records: List of record dictionaries to send
            endpoint: API endpoint path
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            API response data
            
        Raises:
            APIError: If all retry attempts fail
        """
        if max_retries is None:
            max_retries = self.config.max_retries
        
        last_error = None
        auth_refreshed = False
        
        for attempt in range(max_retries + 1):
            try:
                return self.send_batch(records, endpoint, timeout)
                
            except AuthenticationError as e:
                # Try to refresh authentication token once
                if not auth_refreshed:
                    try:
                        self.logger.info("Refreshing authentication token")
                        self.authenticator.refresh_token_with_retry()
                        auth_refreshed = True
                        # Don't count this as a failed attempt
                        continue
                    except Exception as auth_error:
                        self.logger.error(f"Token refresh failed: {auth_error}")
                        raise APIError(f"Authentication refresh failed: {auth_error}")
                else:
                    raise APIError(f"Authentication failed after refresh: {e}")
                    
            except APIError as e:
                last_error = e
                if attempt < max_retries:
                    delay = exponential_backoff(attempt, factor=self.config.retry_backoff_factor)
                    self.logger.warning(
                        f"Batch send attempt {attempt + 1} failed, "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"All batch send attempts failed: {e}")
        
        raise APIError(f"Failed to send batch after {max_retries} attempts: {last_error}")
    
    def process_records_in_batches(self, records: List[Dict[str, Any]], 
                                  endpoint: str = "/api/records",
                                  batch_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """Process records by splitting into batches and sending to API.
        
        Args:
            records: List of all records to process
            endpoint: API endpoint path
            batch_size: Batch size (uses config default if None)
            
        Returns:
            List of all API responses
            
        Raises:
            APIError: If any batch fails to send
        """
        if not records:
            self.logger.info("No records to process")
            return []
        
        if batch_size is None:
            batch_size = self.config.max_batch_size
        
        # Validate batch size
        if batch_size <= 0 or batch_size > self.config.max_batch_size:
            batch_size = self.config.max_batch_size
        
        total_records = len(records)
        batches = list(chunk_list(records, batch_size))
        total_batches = len(batches)
        
        self.logger.info(
            f"Processing {total_records} records in {total_batches} batches "
            f"(batch size: {batch_size})"
        )
        
        responses = []
        failed_batches = []
        
        for batch_num, batch in enumerate(batches, 1):
            try:
                self.logger.debug(f"Processing batch {batch_num}/{total_batches}")
                response = self.send_batch_with_retry(batch, endpoint)
                responses.append(response)
                
                # Log progress for large datasets
                if batch_num % 10 == 0 or batch_num == total_batches:
                    self.logger.info(
                        f"Processed batch {batch_num}/{total_batches} "
                        f"({batch_num * batch_size}/{total_records} records)"
                    )
                    
            except Exception as e:
                error_info = {
                    'batch_number': batch_num,
                    'batch_size': len(batch),
                    'error': str(e),
                    'records': batch
                }
                failed_batches.append(error_info)
                
                self.logger.error(
                    f"Failed to process batch {batch_num}/{total_batches}: {e}"
                )
        
        # Report results
        successful_batches = len(responses)
        failed_count = len(failed_batches)
        
        self.logger.info(
            f"Batch processing complete: {successful_batches} successful, "
            f"{failed_count} failed"
        )
        
        if failed_batches:
            # Log failed batches for manual retry
            self.logger.error(f"Failed batches: {failed_batches}")
            raise APIError(
                f"Failed to process {failed_count} out of {total_batches} batches"
            )
        
        return responses
    
    def health_check(self, timeout: int = 10) -> bool:
        """Perform API health check.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            url = f"{self.config.api_base_url.rstrip('/')}/health"
            response = self.session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                self.logger.info("API health check passed")
                return True
            else:
                self.logger.warning(f"API health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.warning(f"API health check failed: {e}")
            return False