"""Monitoring and metrics collection for LivevoxMetadata processing."""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class ProcessingMetrics:
    """Container for processing metrics."""
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    files_processed: int = 0
    files_failed: int = 0
    records_processed: int = 0
    batches_sent: int = 0
    api_requests_successful: int = 0
    api_requests_failed: int = 0
    s3_operations_successful: int = 0
    s3_operations_failed: int = 0
    auth_refreshes: int = 0
    total_processing_time: float = 0.0
    peak_memory_usage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'files_processed': self.files_processed,
            'files_failed': self.files_failed,
            'files_total': self.files_total,
            'success_rate': self.success_rate,
            'records_processed': self.records_processed,
            'records_per_second': self.records_per_second,
            'batches_sent': self.batches_sent,
            'api_requests_successful': self.api_requests_successful,
            'api_requests_failed': self.api_requests_failed,
            'api_success_rate': self.api_success_rate,
            's3_operations_successful': self.s3_operations_successful,
            's3_operations_failed': self.s3_operations_failed,
            's3_success_rate': self.s3_success_rate,
            'auth_refreshes': self.auth_refreshes,
            'peak_memory_mb': self.peak_memory_usage
        }
    
    @property
    def duration_seconds(self) -> float:
        """Calculate processing duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.utcnow() - self.start_time).total_seconds()
        return 0.0
    
    @property
    def files_total(self) -> int:
        """Total files attempted."""
        return self.files_processed + self.files_failed
    
    @property
    def success_rate(self) -> float:
        """File processing success rate as percentage."""
        total = self.files_total
        return (self.files_processed / total * 100) if total > 0 else 0.0
    
    @property
    def records_per_second(self) -> float:
        """Records processed per second."""
        duration = self.duration_seconds
        return self.records_processed / duration if duration > 0 else 0.0
    
    @property
    def api_success_rate(self) -> float:
        """API request success rate as percentage."""
        total = self.api_requests_successful + self.api_requests_failed
        return (self.api_requests_successful / total * 100) if total > 0 else 0.0
    
    @property
    def s3_success_rate(self) -> float:
        """S3 operation success rate as percentage."""
        total = self.s3_operations_successful + self.s3_operations_failed
        return (self.s3_operations_successful / total * 100) if total > 0 else 0.0


class PerformanceMonitor:
    """Monitor and track performance metrics during processing."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = ProcessingMetrics()
        self._lock = Lock()
        self.logger = logging.getLogger(__name__)
    
    def start_processing(self) -> None:
        """Mark the start of processing."""
        with self._lock:
            self.metrics.start_time = datetime.utcnow()
            self.logger.info("Processing started")
    
    def end_processing(self) -> None:
        """Mark the end of processing."""
        with self._lock:
            self.metrics.end_time = datetime.utcnow()
            duration = self.metrics.duration_seconds
            self.logger.info(f"Processing completed in {duration:.2f} seconds")
    
    def record_file_success(self, processing_time: float = 0.0, records_count: int = 0) -> None:
        """Record successful file processing."""
        with self._lock:
            self.metrics.files_processed += 1
            self.metrics.records_processed += records_count
            self.metrics.total_processing_time += processing_time
    
    def record_file_failure(self) -> None:
        """Record failed file processing."""
        with self._lock:
            self.metrics.files_failed += 1
    
    def record_batch_sent(self, batch_size: int) -> None:
        """Record successful batch sending."""
        with self._lock:
            self.metrics.batches_sent += 1
            self.metrics.api_requests_successful += 1
    
    def record_api_failure(self) -> None:
        """Record API request failure."""
        with self._lock:
            self.metrics.api_requests_failed += 1
    
    def record_s3_success(self) -> None:
        """Record successful S3 operation."""
        with self._lock:
            self.metrics.s3_operations_successful += 1
    
    def record_s3_failure(self) -> None:
        """Record failed S3 operation."""
        with self._lock:
            self.s3_operations_failed += 1
    
    def record_auth_refresh(self) -> None:
        """Record authentication token refresh."""
        with self._lock:
            self.metrics.auth_refreshes += 1
    
    def update_memory_usage(self, memory_mb: float) -> None:
        """Update peak memory usage."""
        with self._lock:
            if memory_mb > self.metrics.peak_memory_usage:
                self.metrics.peak_memory_usage = memory_mb
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics as dictionary."""
        with self._lock:
            return self.metrics.to_dict()
    
    def log_progress_summary(self, interval_seconds: int = 60) -> None:
        """Log progress summary periodically."""
        metrics = self.get_current_metrics()
        
        self.logger.info(
            f"Progress Update - "
            f"Files: {metrics['files_processed']}/{metrics['files_total']} "
            f"({metrics['success_rate']:.1f}% success), "
            f"Records: {metrics['records_processed']} "
            f"({metrics['records_per_second']:.1f}/sec), "
            f"Batches: {metrics['batches_sent']}, "
            f"Duration: {metrics['duration_seconds']:.1f}s"
        )
    
    def get_performance_report(self) -> str:
        """Generate comprehensive performance report."""
        metrics = self.get_current_metrics()
        
        report_lines = [
            "=== LivevoxMetadata Processing Performance Report ===",
            f"Processing Duration: {metrics['duration_seconds']:.2f} seconds",
            f"Start Time: {metrics['start_time']}",
            f"End Time: {metrics['end_time'] or 'In Progress'}",
            "",
            "File Processing:",
            f"  - Total Files: {metrics['files_total']}",
            f"  - Successful: {metrics['files_processed']}",
            f"  - Failed: {metrics['files_failed']}",
            f"  - Success Rate: {metrics['success_rate']:.2f}%",
            "",
            "Record Processing:",
            f"  - Total Records: {metrics['records_processed']:,}",
            f"  - Processing Rate: {metrics['records_per_second']:.2f} records/second",
            f"  - Batches Sent: {metrics['batches_sent']}",
            "",
            "API Performance:",
            f"  - Successful Requests: {metrics['api_requests_successful']}",
            f"  - Failed Requests: {metrics['api_requests_failed']}",
            f"  - API Success Rate: {metrics['api_success_rate']:.2f}%",
            "",
            "S3 Performance:",
            f"  - Successful Operations: {metrics['s3_operations_successful']}",
            f"  - Failed Operations: {metrics['s3_operations_failed']}",
            f"  - S3 Success Rate: {metrics['s3_success_rate']:.2f}%",
            "",
            "System:",
            f"  - Auth Refreshes: {metrics['auth_refreshes']}",
            f"  - Peak Memory Usage: {metrics['peak_memory_mb']:.2f} MB",
            "=" * 55
        ]
        
        return "\n".join(report_lines)


class ProgressTracker:
    """Track and report processing progress."""
    
    def __init__(self, total_items: int, report_interval: int = 100):
        """Initialize progress tracker.
        
        Args:
            total_items: Total number of items to process
            report_interval: Report progress every N items
        """
        self.total_items = total_items
        self.processed_items = 0
        self.report_interval = report_interval
        self.start_time = time.time()
        self.last_report_time = self.start_time
        self.logger = logging.getLogger(__name__)
    
    def update(self, count: int = 1) -> None:
        """Update progress counter.
        
        Args:
            count: Number of items processed
        """
        self.processed_items += count
        
        # Report progress at intervals
        if (self.processed_items % self.report_interval == 0 or 
            self.processed_items == self.total_items):
            self._report_progress()
    
    def _report_progress(self) -> None:
        """Report current progress."""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        items_per_second = self.processed_items / elapsed_time if elapsed_time > 0 else 0
        
        percentage = (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0
        
        # Estimate remaining time
        if items_per_second > 0 and self.processed_items < self.total_items:
            remaining_items = self.total_items - self.processed_items
            eta_seconds = remaining_items / items_per_second
            eta_str = f", ETA: {eta_seconds:.0f}s"
        else:
            eta_str = ""
        
        self.logger.info(
            f"Progress: {self.processed_items}/{self.total_items} "
            f"({percentage:.1f}%) - "
            f"{items_per_second:.1f} items/sec{eta_str}"
        )
        
        self.last_report_time = current_time
    
    def finish(self) -> None:
        """Mark processing as complete and log final statistics."""
        end_time = time.time()
        total_time = end_time - self.start_time
        avg_rate = self.processed_items / total_time if total_time > 0 else 0
        
        self.logger.info(
            f"Processing complete: {self.processed_items} items in "
            f"{total_time:.2f}s (avg: {avg_rate:.2f} items/sec)"
        )