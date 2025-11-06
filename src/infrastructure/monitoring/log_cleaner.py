"""日志清理工具

基于时间戳定期删除本地日志文件，遵循零内存存储架构。
"""

import os
import time
import logging
import glob
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta

from .logger_writer import PerformanceMetricsLogger


class LogCleaner:
    """日志清理器
    
    基于配置定期删除过期的日志文件，遵循零内存存储架构。
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[PerformanceMetricsLogger] = None):
        """初始化日志清理器
        
        Args:
            config: 清理配置
            logger: 性能指标日志写入器
        """
        self.config = config
        self.logger = logger or PerformanceMetricsLogger("log_cleaner")
        
        # 默认配置
        self.retention_days = config.get("retention_days", 30)
        self.log_patterns = config.get("log_patterns", [
            "logs/*.log",
            "logs/*.log.*"
        ])
        self.enabled = config.get("enabled", True)
        self.dry_run = config.get("dry_run", False)
        
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """设置日志记录"""
        self.cleaner_logger = logging.getLogger("log_cleaner")
        if not self.cleaner_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.cleaner_logger.addHandler(handler)
            self.cleaner_logger.setLevel(logging.INFO)
    
    def cleanup_logs(self) -> Dict[str, Any]:
        """清理过期日志
        
        Returns:
            清理结果统计
        """
        if not self.enabled:
            self.logger.log_counter("log_cleanup_skipped", 1.0, {"reason": "disabled"})
            return {"status": "skipped", "reason": "disabled"}
        
        start_time = time.time()
        cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
        
        deleted_files = []
        total_size_freed = 0
        errors = []
        
        self.logger.log_timer("log_cleanup_start", 0, {"retention_days": str(self.retention_days)})
        
        try:
            for pattern in self.log_patterns:
                files_deleted, size_freed, pattern_errors = self._cleanup_pattern(pattern, cutoff_time)
                deleted_files.extend(files_deleted)
                total_size_freed += size_freed
                errors.extend(pattern_errors)
            
            # 记录清理结果
            self.logger.log_counter("log_cleanup_files_deleted", len(deleted_files))
            self.logger.log_gauge("log_cleanup_size_freed", total_size_freed)
            
            if errors:
                self.logger.log_counter("log_cleanup_errors", len(errors))
            
            duration = time.time() - start_time
            self.logger.log_timer("log_cleanup_complete", duration, {
                "files_deleted": str(len(deleted_files)),
                "size_freed": str(total_size_freed),
                "errors": str(len(errors))
            })
            
            result = {
                "status": "completed",
                "files_deleted": len(deleted_files),
                "size_freed": total_size_freed,
                "errors": len(errors),
                "duration": duration,
                "deleted_files": deleted_files
            }
            
        except Exception as e:
            self.logger.log_counter("log_cleanup_error", 1.0, {"error": str(e)})
            result = {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time
            }
        
        return result
    
    def _cleanup_pattern(self, pattern: str, cutoff_time: float) -> tuple[List[str], int, List[str]]:
        """清理特定模式的日志文件
        
        Args:
            pattern: 文件模式
            cutoff_time: 截止时间戳
            
        Returns:
            (删除的文件列表, 释放的字节数, 错误列表)
        """
        deleted_files = []
        total_size_freed = 0
        errors = []
        
        try:
            file_paths = glob.glob(pattern)
            
            for file_path in file_paths:
                try:
                    if self._should_delete_file(file_path, cutoff_time):
                        file_size = os.path.getsize(file_path)
                        
                        if self.dry_run:
                            self.cleaner_logger.info(f"[DRY RUN] Would delete: {file_path} ({file_size} bytes)")
                        else:
                            os.remove(file_path)
                            self.cleaner_logger.info(f"Deleted: {file_path} ({file_size} bytes)")
                        
                        deleted_files.append(file_path)
                        total_size_freed += file_size
                        
                except Exception as e:
                    error_msg = f"Error processing {file_path}: {str(e)}"
                    errors.append(error_msg)
                    self.cleaner_logger.error(error_msg)
                    
        except Exception as e:
            error_msg = f"Error processing pattern {pattern}: {str(e)}"
            errors.append(error_msg)
            self.cleaner_logger.error(error_msg)
        
        return deleted_files, total_size_freed, errors
    
    def _should_delete_file(self, file_path: str, cutoff_time: float) -> bool:
        """判断文件是否应该被删除
        
        Args:
            file_path: 文件路径
            cutoff_time: 截止时间戳
            
        Returns:
            是否应该删除
        """
        try:
            # 检查文件修改时间
            file_mtime = os.path.getmtime(file_path)
            
            # 如果文件早于截止时间，则删除
            return file_mtime < cutoff_time
            
        except Exception:
            # 如果无法获取文件时间，为了安全起见不删除
            return False
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """获取清理统计信息
        
        Returns:
            清理统计信息
        """
        return {
            "retention_days": self.retention_days,
            "log_patterns": self.log_patterns,
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "cutoff_time": time.time() - (self.retention_days * 24 * 60 * 60)
        }
    
    def configure(self, config: Dict[str, Any]) -> None:
        """重新配置清理器
        
        Args:
            config: 新的配置
        """
        self.config.update(config)
        self.retention_days = config.get("retention_days", self.retention_days)
        self.log_patterns = config.get("log_patterns", self.log_patterns)
        self.enabled = config.get("enabled", self.enabled)
        self.dry_run = config.get("dry_run", self.dry_run)
        
        self.logger.log_gauge("log_cleaner_config_updated", 1.0, {
            "retention_days": str(self.retention_days),
            "enabled": str(self.enabled)
        })


class ScheduledLogCleaner:
    """定期日志清理器
    
    提供定期检查和清理机制。
    """
    
    def __init__(self, log_cleaner: LogCleaner):
        """初始化定期清理器
        
        Args:
            log_cleaner: 日志清理器实例
        """
        self.log_cleaner = log_cleaner
        self.logger = log_cleaner.logger
        self.last_cleanup_time = 0
        self.cleanup_interval = 24 * 60 * 60  # 24小时（秒）
        
    def check_and_cleanup(self) -> Dict[str, Any]:
        """检查并执行清理
        
        Returns:
            清理结果
        """
        current_time = time.time()
        
        # 检查是否到了清理时间
        if current_time - self.last_cleanup_time < self.cleanup_interval:
            return {
                "status": "skipped",
                "reason": "not_time_yet",
                "next_cleanup_in": self.cleanup_interval - (current_time - self.last_cleanup_time)
            }
        
        # 执行清理
        result = self.log_cleaner.cleanup_logs()
        
        # 更新最后清理时间
        if result["status"] == "completed":
            self.last_cleanup_time = current_time
        
        return result
    
    def force_cleanup(self) -> Dict[str, Any]:
        """强制执行清理
        
        Returns:
            清理结果
        """
        result = self.log_cleaner.cleanup_logs()
        
        if result["status"] == "completed":
            self.last_cleanup_time = time.time()
        
        return result