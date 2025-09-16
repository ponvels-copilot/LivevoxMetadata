# LivevoxMetadata Processing System

A robust data processing system that reads text files from S3, processes them in batches, and sends to API endpoints with JWT authentication.

## Features

- **S3 Integration**: Read text files containing thousands to millions of records
- **Batch Processing**: Process records in configurable batches (max 500 per request)
- **Peak Load Handling**: Optimized for daily volumes with peak processing between 10 AM - 8 PM EST
- **JWT Authentication**: Secure credential management with JWT tokens
- **Error Handling**: Comprehensive failure handling for S3, authentication, and API operations
- **Reliability**: Ensures no records are missed from start to end

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Copy `.env.example` to `.env` and configure:
- AWS credentials and S3 bucket
- API endpoint and JWT configuration
- Processing parameters (batch size, workers, peak hours)
- Retry configuration

## Usage

```python
from src.livevox_metadata.processor import MetadataProcessor

processor = MetadataProcessor()
processor.process_files()
```

## Architecture

- `config.py`: Configuration management
- `s3_client.py`: S3 file reading operations
- `auth.py`: JWT authentication handling
- `api_client.py`: API communication with batching
- `processor.py`: Main processing orchestrator
- `exceptions.py`: Custom exception classes
- `utils.py`: Utility functions