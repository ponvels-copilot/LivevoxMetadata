"""JWT authentication for LivevoxMetadata processing."""

import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from .config import Config
from .exceptions import AuthenticationError
from .utils import exponential_backoff


class JWTAuthenticator:
    """JWT authentication manager."""
    
    def __init__(self, config: Config):
        """Initialize JWT authenticator.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._token_cache: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
    
    def generate_token(self, payload: Optional[Dict[str, Any]] = None, 
                      expires_in_hours: int = 1) -> str:
        """Generate a JWT token.
        
        Args:
            payload: Optional custom payload data
            expires_in_hours: Token expiration time in hours
            
        Returns:
            Generated JWT token
            
        Raises:
            AuthenticationError: If token generation fails
        """
        try:
            current_time = datetime.utcnow()
            expiry_time = current_time + timedelta(hours=expires_in_hours)
            
            token_payload = {
                'iat': current_time,
                'exp': expiry_time,
                'iss': 'livevox-metadata-processor',
                'sub': 'data-processing'
            }
            
            if payload:
                token_payload.update(payload)
            
            token = jwt.encode(
                token_payload,
                self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm
            )
            
            self.logger.debug(f"Generated JWT token expiring at {expiry_time}")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to generate JWT token: {e}")
            raise AuthenticationError(f"Token generation failed: {e}")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate a JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationError: If token validation fails
        """
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            
            self.logger.debug("JWT token validation successful")
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("JWT token has expired")
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            self.logger.error(f"Invalid JWT token: {e}")
            raise AuthenticationError(f"Invalid token: {e}")
    
    def get_valid_token(self, force_refresh: bool = False) -> str:
        """Get a valid JWT token, using cache when possible.
        
        Args:
            force_refresh: Force generation of new token even if cached token is valid
            
        Returns:
            Valid JWT token
            
        Raises:
            AuthenticationError: If token retrieval fails
        """
        current_time = datetime.utcnow()
        
        # Check if cached token is still valid (with 5-minute buffer)
        if (not force_refresh and 
            self._token_cache and 
            self._token_expiry and 
            current_time < self._token_expiry - timedelta(minutes=5)):
            
            self.logger.debug("Using cached JWT token")
            return self._token_cache
        
        # Generate new token
        try:
            token = self.generate_token()
            self._token_cache = token
            self._token_expiry = current_time + timedelta(hours=1)
            
            self.logger.info("Generated new JWT token")
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to get valid token: {e}")
            raise AuthenticationError(f"Token retrieval failed: {e}")
    
    def get_auth_headers(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get authorization headers with JWT token.
        
        Args:
            force_refresh: Force generation of new token
            
        Returns:
            Dictionary with Authorization header
            
        Raises:
            AuthenticationError: If token retrieval fails
        """
        token = self.get_valid_token(force_refresh)
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def refresh_token_with_retry(self, max_retries: Optional[int] = None) -> str:
        """Refresh JWT token with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            New JWT token
            
        Raises:
            AuthenticationError: If all retry attempts fail
        """
        if max_retries is None:
            max_retries = self.config.max_retries
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return self.get_valid_token(force_refresh=True)
                
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    delay = exponential_backoff(attempt, factor=self.config.retry_backoff_factor)
                    self.logger.warning(
                        f"Token refresh attempt {attempt + 1} failed, "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"All token refresh attempts failed: {e}")
        
        raise AuthenticationError(f"Token refresh failed after {max_retries} attempts: {last_error}")