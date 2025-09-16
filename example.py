#!/usr/bin/env python3
"""
Example script demonstrating LivevoxMetadata processing.

This script shows how to use the LivevoxMetadata processor to:
1. Read text files from S3
2. Process them in batches 
3. Send to API endpoints with JWT authentication
"""

import os
from src.livevox_metadata.processor import MetadataProcessor
from src.livevox_metadata.exceptions import LivevoxMetadataError


def main():
    """Run example processing."""
    
    print("LivevoxMetadata Processing System Example")
    print("=" * 45)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ No .env file found. Please copy .env.example to .env and configure it.")
        print("\nRequired configuration:")
        print("- AWS credentials and S3 bucket")
        print("- API endpoint URL")
        print("- JWT secret key")
        return 1
    
    try:
        # Initialize processor
        print("📋 Initializing processor...")
        processor = MetadataProcessor(log_level='INFO')
        
        # Example: List files that would be processed
        print("📁 Listing available files...")
        files = processor.s3_client.list_files()
        
        if not files:
            print("⚠️  No text files found in S3 bucket")
            return 0
        
        print(f"📊 Found {len(files)} files:")
        for file_info in files[:5]:  # Show first 5 files
            size_mb = file_info['size'] / (1024 * 1024)
            print(f"   - {file_info['key']} ({size_mb:.2f} MB)")
        
        if len(files) > 5:
            print(f"   ... and {len(files) - 5} more files")
        
        # Example: Process a limited number of files for demonstration
        print(f"\n🚀 Processing first 2 files for demonstration...")
        
        results = processor.process_files(
            max_files=2  # Limit to 2 files for example
        )
        
        print(f"\n✅ Processing completed!")
        print(f"📊 Results Summary:")
        print(f"   - Total files: {results['total_files']}")
        print(f"   - Successful: {results['successful_files']}")
        print(f"   - Failed: {results['failed_files']}")
        print(f"   - Records processed: {results['total_records_processed']}")
        print(f"   - API batches sent: {results['total_batches_sent']}")
        
        if results['processing_duration_seconds']:
            print(f"   - Processing time: {results['processing_duration_seconds']:.2f} seconds")
        
        return 0 if results['overall_success'] else 1
        
    except LivevoxMetadataError as e:
        print(f"❌ Processing error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())