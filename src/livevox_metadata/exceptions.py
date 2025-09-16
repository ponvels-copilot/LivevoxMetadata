"""Custom exceptions for LivevoxMetadata processing."""


class LivevoxMetadataError(Exception):
    """Base exception for LivevoxMetadata processing."""
    pass


class S3Error(LivevoxMetadataError):
    """Exception raised for S3 operation errors."""
    pass


class AuthenticationError(LivevoxMetadataError):
    """Exception raised for authentication failures."""
    pass


class APIError(LivevoxMetadataError):
    """Exception raised for API communication errors."""
    pass


class ConfigurationError(LivevoxMetadataError):
    """Exception raised for configuration errors."""
    pass


class BatchProcessingError(LivevoxMetadataError):
    """Exception raised for batch processing errors."""
    pass