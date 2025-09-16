"""Command-line interface for LivevoxMetadata processing."""

import argparse
import sys
import json
from typing import Optional

from .processor import MetadataProcessor
from .exceptions import LivevoxMetadataError


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='LivevoxMetadata Processing System - Process S3 text files and send to API endpoints'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to .env configuration file'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--file-prefix', '-p',
        type=str,
        default='',
        help='S3 key prefix to filter files (default: empty - process all files)'
    )
    
    parser.add_argument(
        '--file-pattern', '-f',
        type=str,
        default='.txt',
        help='File pattern/extension to match (default: .txt)'
    )
    
    parser.add_argument(
        '--max-files', '-m',
        type=int,
        help='Maximum number of files to process (useful for testing)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path for results JSON'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='List files that would be processed without actually processing them'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize processor
        processor = MetadataProcessor(
            config_file=args.config,
            log_level=args.log_level
        )
        
        if args.dry_run:
            # Just list files without processing
            files = processor.s3_client.list_files(
                prefix=args.file_prefix,
                suffix=args.file_pattern
            )
            
            if args.max_files and len(files) > args.max_files:
                files = files[:args.max_files]
            
            print(f"Found {len(files)} files to process:")
            for file_info in files:
                print(f"  - {file_info['key']} ({file_info['size']} bytes)")
            
            return 0
        
        # Process files
        results = processor.process_files(
            file_prefix=args.file_prefix,
            file_pattern=args.file_pattern,
            max_files=args.max_files
        )
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results written to {args.output}")
        else:
            print("\nProcessing Results:")
            print(f"  Total files: {results['total_files']}")
            print(f"  Successful: {results['successful_files']}")
            print(f"  Failed: {results['failed_files']}")
            print(f"  Records processed: {results['total_records_processed']}")
            print(f"  Batches sent: {results['total_batches_sent']}")
            
            if results['processing_duration_seconds']:
                print(f"  Duration: {results['processing_duration_seconds']:.2f} seconds")
        
        # Exit with error code if any files failed
        if not results['overall_success']:
            print("\nSome files failed to process. Check logs for details.", file=sys.stderr)
            return 1
        
        return 0
        
    except LivevoxMetadataError as e:
        print(f"Processing error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())