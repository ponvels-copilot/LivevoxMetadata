"""Data validation utilities for LivevoxMetadata processing."""

import re
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging

from .exceptions import LivevoxMetadataError


class RecordValidator:
    """Validate and sanitize record data."""
    
    def __init__(self):
        """Initialize record validator."""
        self.logger = logging.getLogger(__name__)
        
        # Common validation patterns
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.phone_pattern = re.compile(r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$')  # US phone format
        self.alphanumeric_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    def validate_record_structure(self, record: Dict[str, Any], 
                                required_fields: Optional[List[str]] = None) -> bool:
        """Validate basic record structure.
        
        Args:
            record: Record dictionary to validate
            required_fields: List of required field names
            
        Returns:
            True if record is valid, False otherwise
        """
        if not isinstance(record, dict):
            self.logger.warning("Record is not a dictionary")
            return False
        
        if not record:
            self.logger.warning("Record is empty")
            return False
        
        # Check required fields
        if required_fields:
            missing_fields = []
            for field in required_fields:
                if field not in record or record[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                self.logger.warning(f"Record missing required fields: {missing_fields}")
                return False
        
        return True
    
    def validate_field_types(self, record: Dict[str, Any], 
                           field_types: Dict[str, type]) -> bool:
        """Validate field data types.
        
        Args:
            record: Record dictionary to validate
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            True if all field types are correct, False otherwise
        """
        type_errors = []
        
        for field_name, expected_type in field_types.items():
            if field_name in record:
                value = record[field_name]
                if value is not None and not isinstance(value, expected_type):
                    type_errors.append(f"{field_name}: expected {expected_type.__name__}, got {type(value).__name__}")
        
        if type_errors:
            self.logger.warning(f"Record type validation errors: {type_errors}")
            return False
        
        return True
    
    def validate_email(self, email: str) -> bool:
        """Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        if not isinstance(email, str):
            return False
        
        return bool(self.email_pattern.match(email.strip().lower()))
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if phone number is valid, False otherwise
        """
        if not isinstance(phone, str):
            return False
        
        # Remove common separators and whitespace
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        return bool(self.phone_pattern.match(cleaned_phone))
    
    def sanitize_string_field(self, value: str, max_length: int = 255,
                            allow_special_chars: bool = True) -> str:
        """Sanitize string field value.
        
        Args:
            value: String value to sanitize
            max_length: Maximum allowed length
            allow_special_chars: Whether to allow special characters
            
        Returns:
            Sanitized string value
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Basic sanitization
        value = value.strip()
        
        # Remove or escape special characters if not allowed
        if not allow_special_chars:
            value = re.sub(r'[^\w\s-]', '', value)
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length].rstrip()
        
        return value
    
    def validate_and_sanitize_record(self, record: Dict[str, Any],
                                   validation_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate and sanitize a complete record.
        
        Args:
            record: Record dictionary to validate and sanitize
            validation_rules: Dictionary of validation rules per field
            
        Returns:
            Sanitized record dictionary
            
        Raises:
            LivevoxMetadataError: If record fails critical validation
        """
        if not self.validate_record_structure(record):
            raise LivevoxMetadataError("Record failed basic structure validation")
        
        sanitized_record = {}
        
        for key, value in record.items():
            try:
                # Apply field-specific validation and sanitization
                if validation_rules and key in validation_rules:
                    rules = validation_rules[key]
                    
                    # Type validation
                    if 'type' in rules and value is not None:
                        expected_type = rules['type']
                        if not isinstance(value, expected_type):
                            # Try to convert
                            if expected_type == str:
                                value = str(value)
                            elif expected_type == int:
                                value = int(float(value))
                            elif expected_type == float:
                                value = float(value)
                    
                    # String sanitization
                    if isinstance(value, str):
                        max_length = rules.get('max_length', 255)
                        allow_special = rules.get('allow_special_chars', True)
                        value = self.sanitize_string_field(value, max_length, allow_special)
                    
                    # Email validation
                    if rules.get('validate_email', False) and value:
                        if not self.validate_email(value):
                            self.logger.warning(f"Invalid email in field {key}: {value}")
                            continue  # Skip invalid email
                    
                    # Phone validation
                    if rules.get('validate_phone', False) and value:
                        if not self.validate_phone(value):
                            self.logger.warning(f"Invalid phone in field {key}: {value}")
                            continue  # Skip invalid phone
                
                sanitized_record[key] = value
                
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Failed to sanitize field {key}: {e}")
                # Skip problematic fields rather than failing entire record
                continue
        
        # Add processing metadata
        sanitized_record['_processed_at'] = datetime.utcnow().isoformat()
        sanitized_record['_validation_passed'] = True
        
        return sanitized_record


class DataQualityChecker:
    """Check data quality and generate reports."""
    
    def __init__(self):
        """Initialize data quality checker."""
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'field_errors': {},
            'validation_errors': []
        }
    
    def check_record_quality(self, record: Dict[str, Any], 
                           quality_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check quality of a single record.
        
        Args:
            record: Record to check
            quality_rules: Quality checking rules
            
        Returns:
            Quality report dictionary
        """
        self.stats['total_records'] += 1
        
        quality_report = {
            'record_id': record.get('id', 'unknown'),
            'is_valid': True,
            'quality_score': 100.0,
            'issues': []
        }
        
        if not record:
            quality_report['is_valid'] = False
            quality_report['quality_score'] = 0.0
            quality_report['issues'].append('Empty record')
            self.stats['invalid_records'] += 1
            return quality_report
        
        # Check for required fields
        if quality_rules and 'required_fields' in quality_rules:
            for field in quality_rules['required_fields']:
                if field not in record or record[field] is None or record[field] == '':
                    quality_report['issues'].append(f'Missing required field: {field}')
                    quality_report['quality_score'] -= 20
                    
                    # Track field error stats
                    if field not in self.stats['field_errors']:
                        self.stats['field_errors'][field] = 0
                    self.stats['field_errors'][field] += 1
        
        # Check data types
        if quality_rules and 'field_types' in quality_rules:
            for field, expected_type in quality_rules['field_types'].items():
                if field in record and record[field] is not None:
                    if not isinstance(record[field], expected_type):
                        quality_report['issues'].append(
                            f'Incorrect type for {field}: expected {expected_type.__name__}'
                        )
                        quality_report['quality_score'] -= 10
        
        # Check field completeness
        total_fields = len(record) if isinstance(record, dict) else 0
        empty_fields = sum(1 for v in record.values() if v is None or v == '') if total_fields > 0 else 0
        
        if total_fields > 0:
            completeness = (total_fields - empty_fields) / total_fields * 100
            quality_report['completeness_percentage'] = completeness
            
            if completeness < 50:
                quality_report['issues'].append(f'Low data completeness: {completeness:.1f}%')
                quality_report['quality_score'] -= 30
        
        # Determine if record is valid based on quality score
        if quality_report['quality_score'] < 50:
            quality_report['is_valid'] = False
            self.stats['invalid_records'] += 1
        else:
            self.stats['valid_records'] += 1
        
        # Store validation errors for reporting
        if quality_report['issues']:
            self.stats['validation_errors'].extend(quality_report['issues'])
        
        return quality_report
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get overall data quality summary.
        
        Returns:
            Quality summary dictionary
        """
        total = self.stats['total_records']
        valid_rate = (self.stats['valid_records'] / total * 100) if total > 0 else 0
        
        # Find most common field errors
        top_field_errors = sorted(
            self.stats['field_errors'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_records_checked': total,
            'valid_records': self.stats['valid_records'],
            'invalid_records': self.stats['invalid_records'],
            'validation_rate_percentage': valid_rate,
            'top_field_errors': top_field_errors,
            'unique_validation_errors': len(set(self.stats['validation_errors'])),
            'quality_status': 'Good' if valid_rate >= 90 else 'Poor' if valid_rate < 50 else 'Acceptable'
        }
    
    def reset_stats(self) -> None:
        """Reset quality checking statistics."""
        self.stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'field_errors': {},
            'validation_errors': []
        }