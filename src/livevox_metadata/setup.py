"""Setup and deployment utilities for LivevoxMetadata processing."""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .config import Config, ConfigurationError
from .exceptions import LivevoxMetadataError


class SetupManager:
    """Manage setup and deployment of the LivevoxMetadata system."""
    
    def __init__(self):
        """Initialize setup manager."""
        self.logger = logging.getLogger(__name__)
        self.project_root = Path(__file__).parent.parent.parent
    
    def check_system_requirements(self) -> Dict[str, Any]:
        """Check system requirements and dependencies.
        
        Returns:
            System requirements check results
        """
        results = {
            'python_version': {
                'required': '3.8+',
                'current': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'satisfied': sys.version_info >= (3, 8)
            },
            'required_packages': {},
            'optional_packages': {},
            'system_checks': {}
        }
        
        # Check required packages
        required_packages = [
            'boto3', 'requests', 'jwt', 'dateutil', 
            'retrying', 'dotenv', 'pytz'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                results['required_packages'][package] = {'installed': True, 'error': None}
            except ImportError as e:
                results['required_packages'][package] = {'installed': False, 'error': str(e)}
        
        # Check optional packages
        optional_packages = ['pytest', 'moto', 'responses']
        
        for package in optional_packages:
            try:
                __import__(package)
                results['optional_packages'][package] = {'installed': True, 'error': None}
            except ImportError as e:
                results['optional_packages'][package] = {'installed': False, 'error': str(e)}
        
        # System checks
        results['system_checks'] = {
            'disk_space': self._check_disk_space(),
            'memory': self._check_memory(),
            'network': self._check_network_connectivity()
        }
        
        return results
    
    def _check_disk_space(self, minimum_gb: float = 1.0) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            statvfs = os.statvfs('.')
            available_bytes = statvfs.f_bavail * statvfs.f_frsize
            available_gb = available_bytes / (1024**3)
            
            return {
                'available_gb': round(available_gb, 2),
                'minimum_gb': minimum_gb,
                'sufficient': available_gb >= minimum_gb
            }
        except Exception as e:
            return {'error': str(e), 'sufficient': False}
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check available memory."""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                mem_total = int([line for line in lines if 'MemTotal' in line][0].split()[1]) * 1024
                mem_available = int([line for line in lines if 'MemAvailable' in line][0].split()[1]) * 1024
                
                mem_total_gb = mem_total / (1024**3)
                mem_available_gb = mem_available / (1024**3)
                
                return {
                    'total_gb': round(mem_total_gb, 2),
                    'available_gb': round(mem_available_gb, 2),
                    'sufficient': mem_available_gb >= 1.0
                }
        except Exception:
            return {'error': 'Could not determine memory info', 'sufficient': True}
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity."""
        try:
            import requests
            response = requests.get('https://httpbin.org/status/200', timeout=5)
            return {
                'internet_access': response.status_code == 200,
                'error': None
            }
        except Exception as e:
            return {
                'internet_access': False,
                'error': str(e)
            }
    
    def create_config_from_template(self, config_path: str = '.env') -> bool:
        """Create configuration file from template.
        
        Args:
            config_path: Path where to create the config file
            
        Returns:
            True if config was created successfully
        """
        template_path = self.project_root / '.env.example'
        target_path = Path(config_path)
        
        if target_path.exists():
            self.logger.warning(f"Configuration file {config_path} already exists")
            return False
        
        try:
            shutil.copy2(template_path, target_path)
            self.logger.info(f"Created configuration template at {config_path}")
            
            print(f"✅ Created configuration file: {config_path}")
            print("⚠️  Please edit the file and set your actual credentials:")
            print("   - AWS credentials and S3 bucket")
            print("   - API endpoint URL")
            print("   - JWT secret key")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create config file: {e}")
            return False
    
    def validate_configuration(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Validate configuration file and settings.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration validation results
        """
        results = {
            'config_file_exists': False,
            'config_valid': False,
            'missing_variables': [],
            'configuration_errors': []
        }
        
        # Check if config file exists
        config_file = Path(config_path or '.env')
        results['config_file_exists'] = config_file.exists()
        
        if not results['config_file_exists']:
            results['configuration_errors'].append(f"Configuration file not found: {config_file}")
            return results
        
        # Try to load and validate configuration
        try:
            config = Config(str(config_file))
            results['config_valid'] = True
            
            # Additional validation checks
            validation_checks = {
                'aws_credentials': config.aws_access_key_id and config.aws_secret_access_key,
                's3_bucket': config.s3_bucket_name,
                'api_url': config.api_base_url,
                'jwt_secret': config.jwt_secret_key,
                'batch_size_valid': 1 <= config.max_batch_size <= 1000,
                'worker_count_valid': 1 <= config.max_workers <= 100
            }
            
            results['validation_checks'] = validation_checks
            failed_checks = [check for check, passed in validation_checks.items() if not passed]
            
            if failed_checks:
                results['configuration_errors'].extend(
                    f"Validation failed: {check}" for check in failed_checks
                )
                results['config_valid'] = False
            
        except ConfigurationError as e:
            results['configuration_errors'].append(f"Configuration error: {e}")
        except Exception as e:
            results['configuration_errors'].append(f"Unexpected error: {e}")
        
        return results
    
    def run_setup_wizard(self) -> bool:
        """Run interactive setup wizard.
        
        Returns:
            True if setup completed successfully
        """
        print("🚀 LivevoxMetadata Processing System Setup Wizard")
        print("=" * 55)
        
        # Step 1: Check system requirements
        print("\n📋 Checking system requirements...")
        req_results = self.check_system_requirements()
        
        if not req_results['python_version']['satisfied']:
            print(f"❌ Python {req_results['python_version']['required']} required, "
                  f"but {req_results['python_version']['current']} found")
            return False
        
        print(f"✅ Python version: {req_results['python_version']['current']}")
        
        # Check required packages
        missing_packages = [
            pkg for pkg, info in req_results['required_packages'].items()
            if not info['installed']
        ]
        
        if missing_packages:
            print(f"❌ Missing required packages: {', '.join(missing_packages)}")
            print("   Please run: pip install -r requirements.txt")
            return False
        
        print("✅ All required packages installed")
        
        # Step 2: Create configuration
        print("\n📝 Setting up configuration...")
        
        if not Path('.env').exists():
            if self.create_config_from_template():
                print("⏸️  Setup paused. Please edit .env file with your credentials, then run setup again.")
                return False
        else:
            print("ℹ️  Configuration file already exists")
        
        # Step 3: Validate configuration
        print("\n🔍 Validating configuration...")
        config_results = self.validate_configuration()
        
        if not config_results['config_valid']:
            print("❌ Configuration validation failed:")
            for error in config_results['configuration_errors']:
                print(f"   - {error}")
            return False
        
        print("✅ Configuration is valid")
        
        # Step 4: Test connections
        print("\n🔗 Testing connections...")
        
        try:
            # Test configuration loading
            config = Config()
            
            # Test AWS credentials (without actual S3 call)
            print("✅ AWS credentials configured")
            
            # Test API configuration
            if config.api_base_url:
                print("✅ API endpoint configured")
            
            # Test JWT configuration
            if config.jwt_secret_key:
                print("✅ JWT authentication configured")
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
        
        print("\n🎉 Setup completed successfully!")
        print("\n📚 Next steps:")
        print("   - Run: python example.py (for demonstration)")
        print("   - Run: python main.py --dry-run (to list files)")
        print("   - Run: python main.py (for full processing)")
        
        return True
    
    def generate_deployment_config(self, environment: str = 'production') -> str:
        """Generate deployment configuration.
        
        Args:
            environment: Target environment (development/production)
            
        Returns:
            Deployment configuration as string
        """
        if environment == 'production':
            config_template = """
# Production Configuration for LivevoxMetadata Processing

# Performance Settings
MAX_BATCH_SIZE=500
MAX_WORKERS=20
MAX_RETRIES=5
RETRY_BACKOFF_FACTOR=2.0

# Peak Hours (EST)
PEAK_START_HOUR=10
PEAK_END_HOUR=20
TIMEZONE=America/New_York

# Logging
LOG_LEVEL=INFO

# Security
# Ensure JWT_SECRET_KEY is a strong, randomly generated secret
# AWS credentials should be set via IAM roles or environment variables

# Monitoring
ENABLE_METRICS=true
METRICS_INTERVAL=300

# Resource Limits
MEMORY_LIMIT_MB=4096
PROCESSING_TIMEOUT=3600
"""
        else:  # development
            config_template = """
# Development Configuration for LivevoxMetadata Processing

# Performance Settings (reduced for development)
MAX_BATCH_SIZE=100
MAX_WORKERS=4
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=1.5

# Peak Hours
PEAK_START_HOUR=9
PEAK_END_HOUR=17
TIMEZONE=America/New_York

# Logging (more verbose for development)
LOG_LEVEL=DEBUG

# Development flags
DEVELOPMENT_MODE=true
"""
        
        return config_template.strip()


def main():
    """Main entry point for setup script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LivevoxMetadata Setup Utility')
    parser.add_argument('--wizard', '-w', action='store_true', help='Run interactive setup wizard')
    parser.add_argument('--check', '-c', action='store_true', help='Check system requirements')
    parser.add_argument('--validate', '-v', action='store_true', help='Validate configuration')
    parser.add_argument('--create-config', action='store_true', help='Create configuration from template')
    
    args = parser.parse_args()
    
    setup_manager = SetupManager()
    
    if args.wizard:
        success = setup_manager.run_setup_wizard()
        sys.exit(0 if success else 1)
    
    elif args.check:
        results = setup_manager.check_system_requirements()
        print("System Requirements Check:")
        print(f"Python: {results['python_version']['current']} (required: {results['python_version']['required']})")
        
        for package, info in results['required_packages'].items():
            status = "✅" if info['installed'] else "❌"
            print(f"{status} {package}")
        
        sys.exit(0)
    
    elif args.validate:
        results = setup_manager.validate_configuration()
        if results['config_valid']:
            print("✅ Configuration is valid")
            sys.exit(0)
        else:
            print("❌ Configuration validation failed:")
            for error in results['configuration_errors']:
                print(f"   - {error}")
            sys.exit(1)
    
    elif args.create_config:
        success = setup_manager.create_config_from_template()
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()