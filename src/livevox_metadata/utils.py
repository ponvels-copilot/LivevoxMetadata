"""Utility functions for LivevoxMetadata processing."""

import logging
import time
from datetime import datetime
from typing import Any, List, TypeVar, Iterator
import pytz

T = TypeVar('T')


def setup_logging(level: str = 'INFO') -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger('livevox_metadata')


def chunk_list(items: List[T], chunk_size: int) -> Iterator[List[T]]:
    """Split a list into chunks of specified size.
    
    Args:
        items: List to split
        chunk_size: Maximum size of each chunk
        
    Yields:
        Chunks of the original list
    """
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def is_peak_hour(timezone_name: str = 'America/New_York', 
                 start_hour: int = 10, 
                 end_hour: int = 20) -> bool:
    """Check if current time is within peak processing hours.
    
    Args:
        timezone_name: Timezone name (e.g., 'America/New_York')
        start_hour: Peak start hour (24-hour format)
        end_hour: Peak end hour (24-hour format)
        
    Returns:
        True if current time is within peak hours
    """
    try:
        tz = pytz.timezone(timezone_name)
        current_time = datetime.now(tz)
        current_hour = current_time.hour
        
        if start_hour <= end_hour:
            return start_hour <= current_hour < end_hour
        else:
            # Handle case where peak hours span midnight
            return current_hour >= start_hour or current_hour < end_hour
    except Exception:
        # Default to True if timezone calculation fails
        return True


def exponential_backoff(attempt: int, base_delay: float = 1.0, factor: float = 2.0) -> float:
    """Calculate exponential backoff delay.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        factor: Multiplication factor for each attempt
        
    Returns:
        Delay time in seconds
    """
    return base_delay * (factor ** attempt)


def safe_json_loads(data: str, default: Any = None) -> Any:
    """Safely parse JSON string.
    
    Args:
        data: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON data or default value
    """
    import json
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def validate_batch_size(batch_size: int, max_size: int = 500) -> int:
    """Validate and adjust batch size.
    
    Args:
        batch_size: Requested batch size
        max_size: Maximum allowed batch size
        
    Returns:
        Valid batch size
    """
    if batch_size <= 0:
        return 1
    if batch_size > max_size:
        return max_size
    return batch_size


def get_timestamp() -> str:
    """Get current timestamp as ISO format string.
    
    Returns:
        ISO format timestamp string
    """
    return datetime.utcnow().isoformat() + 'Z'