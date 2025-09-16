# LivevoxMetadata Processing System

A robust, production-ready data processing system that reads text files from Amazon S3, processes them in configurable batches, and sends to API endpoints with JWT authentication. Designed to handle daily volumes ranging from thousands to millions of records with peak load optimization.

## 🚀 Features

### Core Capabilities
- **Scalable S3 Integration**: Efficiently read and process text files containing thousands to millions of records
- **Intelligent Batch Processing**: Configurable batch sizes (default max 500 records per API request) with automatic chunking
- **Peak Load Optimization**: Automatically adjusts processing parallelism during peak hours (10 AM - 8 PM EST)
- **Secure JWT Authentication**: Token generation, validation, caching, and automatic refresh
- **Comprehensive Error Handling**: Separate error handling for S3, authentication, and API operations with exponential backoff retry logic
- **Zero Data Loss**: Robust error recovery mechanisms ensure no records are missed from start to end
- **Real-time Monitoring**: Detailed logging, progress tracking, and performance metrics
- **Production Ready**: Memory-efficient streaming, configurable timeouts, and resource management

### Advanced Features
- **Data Validation**: Built-in record validation and sanitization with customizable rules
- **Quality Monitoring**: Data quality checking and reporting
- **Flexible Configuration**: Environment-based configuration with validation
- **CLI Interface**: Command-line interface with dry-run capability
- **Interactive Setup**: Setup wizard for easy deployment
- **Parallel Processing**: Multi-threaded processing with configurable worker counts

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- AWS account with S3 access
- API endpoint for data submission

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd LivevoxMetadata
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run setup wizard:**
   ```bash
   python setup.py --wizard
   ```

4. **Configure your environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

### Manual Setup

1. **Check system requirements:**
   ```bash
   python setup.py --check
   ```

2. **Create configuration file:**
   ```bash
   python setup.py --create-config
   ```

3. **Validate configuration:**
   ```bash
   python setup.py --validate
   ```

## ⚙️ Configuration

### Required Environment Variables

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# API Configuration
API_BASE_URL=https://your-api-endpoint.com
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256

# Processing Configuration
MAX_BATCH_SIZE=500
MAX_WORKERS=10
PEAK_START_HOUR=10
PEAK_END_HOUR=20
TIMEZONE=America/New_York

# Retry Configuration
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=2
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_BATCH_SIZE` | 500 | Maximum records per API batch |
| `MAX_WORKERS` | 10 | Maximum parallel processing workers |
| `PEAK_START_HOUR` | 10 | Peak processing start hour (24h format) |
| `PEAK_END_HOUR` | 20 | Peak processing end hour (24h format) |
| `TIMEZONE` | America/New_York | Timezone for peak hour calculations |
| `MAX_RETRIES` | 3 | Maximum retry attempts for failed operations |
| `RETRY_BACKOFF_FACTOR` | 2.0 | Exponential backoff multiplier |

## 🔧 Usage

### Command Line Interface

```bash
# Process all files
python main.py

# Dry run (list files without processing)
python main.py --dry-run

# Process specific file pattern
python main.py --file-prefix "data/2024/" --file-pattern ".txt"

# Limit files for testing
python main.py --max-files 5

# Save results to JSON
python main.py --output results.json

# Debug mode
python main.py --log-level DEBUG
```

### Programmatic Usage

```python
from src.livevox_metadata.processor import MetadataProcessor

# Initialize processor
processor = MetadataProcessor(log_level='INFO')

# Process files
results = processor.process_files(
    file_prefix='data/',
    file_pattern='.txt',
    max_files=100  # Optional limit for testing
)

# Check results
print(f"Processed {results['successful_files']} files")
print(f"Total records: {results['total_records_processed']}")
```

### Example Script

```bash
# Run the example demonstration
python example.py
```

## 🏗️ Architecture

### Core Components

```
src/livevox_metadata/
├── processor.py        # Main processing orchestrator
├── s3_client.py       # S3 file operations with streaming
├── api_client.py      # API communication with batching
├── auth.py           # JWT authentication management
├── config.py         # Configuration management
├── validation.py     # Data validation and quality checking
├── monitoring.py     # Performance monitoring and metrics
├── utils.py          # Utility functions
├── exceptions.py     # Custom exception classes
└── cli.py           # Command-line interface
```

### Data Flow

1. **S3 Discovery**: List and filter text files from S3 bucket
2. **File Streaming**: Read files line-by-line for memory efficiency
3. **Record Parsing**: Parse lines into structured records (JSON or CSV)
4. **Data Validation**: Validate and sanitize records
5. **Batch Creation**: Group records into configurable batches
6. **JWT Authentication**: Generate/refresh JWT tokens as needed
7. **API Submission**: Send batches to API endpoints with retry logic
8. **Progress Tracking**: Monitor processing and log statistics
9. **Error Recovery**: Handle failures and ensure no data loss

### Processing Features

- **Memory Efficient**: Streams large files without loading entirely into memory
- **Parallel Processing**: Multiple workers process files concurrently
- **Peak Hour Optimization**: Adjusts worker count based on time of day
- **Fault Tolerance**: Comprehensive retry logic for all operations
- **Progress Monitoring**: Real-time progress reporting and statistics

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_basic.py::TestS3Client -v

# Run with coverage
python -m pytest tests/ --cov=src/livevox_metadata
```

### Test Components

- **Unit Tests**: Test individual components (S3, API, Auth, etc.)
- **Integration Tests**: Test component interactions
- **Mocking**: Uses moto for AWS service mocking

### Example Test Data

The tests include mock S3 data and API responses for comprehensive testing without external dependencies.

## 📊 Monitoring

### Built-in Metrics

- **File Processing**: Success/failure rates, processing times
- **Record Processing**: Total records, processing rate, validation errors
- **API Performance**: Request success rates, response times, retry counts
- **S3 Operations**: Read success rates, error rates
- **Authentication**: Token refresh frequency, authentication errors
- **System Resources**: Memory usage, processing duration

### Logging Levels

- **DEBUG**: Detailed operation logs
- **INFO**: Progress updates and summaries
- **WARNING**: Non-critical issues and retry attempts
- **ERROR**: Critical errors requiring attention

### Performance Reporting

```python
# Get performance report
from src.livevox_metadata.monitoring import PerformanceMonitor

monitor = PerformanceMonitor()
# ... process files ...
report = monitor.get_performance_report()
print(report)
```

## 🔒 Security

### JWT Authentication
- Secure token generation with configurable algorithms
- Automatic token refresh and caching
- Configurable token expiration times

### Credential Management
- Environment variable-based configuration
- No hardcoded credentials in source code
- Support for AWS IAM roles

### Data Protection
- Input validation and sanitization
- Secure error handling (no credential leakage)
- Configurable field validation rules

## 📈 Production Deployment

### Performance Tuning

```bash
# High-volume configuration
MAX_BATCH_SIZE=500
MAX_WORKERS=20
MAX_RETRIES=5

# Memory optimization
# Monitor peak memory usage and adjust accordingly
```

### Monitoring Setup

```bash
# Enable detailed logging
LOG_LEVEL=INFO

# Monitor key metrics
# - Processing rate (records/second)
# - Error rates
# - Memory usage
# - API response times
```

### Error Handling

- **S3 Errors**: Automatic retry with exponential backoff
- **API Errors**: Batch retry with authentication refresh
- **Authentication Errors**: Automatic token refresh
- **Network Errors**: Configurable retry attempts
- **Data Errors**: Validation and sanitization with error logging

## 🔧 Troubleshooting

### Common Issues

1. **Configuration Errors**
   ```bash
   python setup.py --validate
   ```

2. **AWS Permission Issues**
   - Ensure S3 read permissions
   - Verify AWS credentials

3. **API Connection Issues**
   - Check API endpoint URL
   - Verify network connectivity
   - Check JWT secret key

4. **Memory Issues**
   - Reduce `MAX_WORKERS`
   - Monitor file sizes
   - Check available system memory

### Debug Mode

```bash
# Enable debug logging
python main.py --log-level DEBUG

# Process limited files for debugging
python main.py --max-files 1 --log-level DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs with DEBUG level
3. Open an issue with system details and error logs