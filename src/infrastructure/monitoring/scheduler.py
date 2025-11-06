"""定期检查调度器

提供定期执行日志清理的调度机制。
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

from .log_cleaner import ScheduledLogCleaner
from .factory import PerformanceMonitorFactory


class LogCleanupScheduler:
    """日志清理调度器
    
    提供定期执行日志清理的调度机制。
    """
    
    def __init__(self, factory: PerformanceMonitorFactory):
        """初始化调度器
        
        Args:
            factory: 性能监控器工厂
        """
        self.factory = factory
        self.logger = logging.getLogger("log_cleanup_scheduler")
        
        # 调度状态
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 调度配置
        self._check_interval_hours = 24  # 默认24小时检查一次
        self._cleanup_time_hour = 2  # 默认凌晨2点执行清理
        
        # 回调函数
        self._cleanup_callback: Optional[Callable] = None
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置调度器
        
        Args:
            config: 配置字典
        """
        self._check_interval_hours = config.get("check_interval_hours", 24)
        self._cleanup_time_hour = config.get("cleanup_time_hour", 2)
        
        self.logger.info(f"调度器配置更新: 检查间隔={self._check_interval_hours}小时, 清理时间={self._cleanup_time_hour}点")
    
    def set_cleanup_callback(self, callback: Callable) -> None:
        """设置清理回调函数
        
        Args:
            callback: 清理完成后的回调函数
        """
        self._cleanup_callback = callback
    
    def start(self) -> None:
        """启动调度器"""
        if self._running:
            self.logger.warning("调度器已经在运行中")
            return
        
        self._running = True
        self._stop_event.clear()
        
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="LogCleanupScheduler",
            daemon=True
        )
        
        self._scheduler_thread.start()
        self.logger.info("日志清理调度器已启动")
    
    def stop(self) -> None:
        """停止调度器"""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=30)
        
        self.logger.info("日志清理调度器已停止")
    
    def _scheduler_loop(self) -> None:
        """调度器主循环"""
        while self._running:
            try:
                # 计算下次清理时间
                next_cleanup_time = self._calculate_next_cleanup_time()
                
                # 等待到清理时间
                wait_time = max(0, (next_cleanup_time - time.time()))
                
                if self._stop_event.wait(timeout=wait_time):
                    # 收到停止信号
                    break
                
                if not self._running:
                    break
                
                # 执行清理
                self._execute_cleanup()
                
            except Exception as e:
                self.logger.error(f"调度器循环出错: {e}")
                # 出错后等待一段时间再继续
                if self._stop_event.wait(timeout=3600):  # 等待1小时
                    break
    
    def _calculate_next_cleanup_time(self) -> float:
        """计算下次清理时间
        
        Returns:
            下次清理时间戳
        """
        now = datetime.now()
        
        # 计算今天的清理时间
        cleanup_time = now.replace(
            hour=self._cleanup_time_hour,
            minute=0,
            second=0,
            microsecond=0
        )
        
        # 如果今天的清理时间已过，则计算明天的
        if cleanup_time <= now:
            cleanup_time += timedelta(days=1)
        
        return cleanup_time.timestamp()
    
    def _execute_cleanup(self) -> None:
        """执行清理"""
        try:
            self.logger.info("开始执行定期日志清理")
            
            # 获取定期清理器
            scheduled_cleaner = self.factory.get_scheduled_cleaner()
            
            if scheduled_cleaner:
                # 执行清理
                result = scheduled_cleaner.check_and_cleanup()
                
                self.logger.info(f"日志清理完成: {result}")
                
                # 调用回调函数
                if self._cleanup_callback:
                    try:
                        self._cleanup_callback(result)
                    except Exception as e:
                        self.logger.error(f"清理回调函数出错: {e}")
            else:
                self.logger.warning("定期清理器未配置")
                
        except Exception as e:
            self.logger.error(f"执行日志清理时出错: {e}")
    
    def force_cleanup(self) -> Dict[str, Any]:
        """强制执行清理
        
        Returns:
            清理结果
        """
        try:
            self.logger.info("执行强制日志清理")
            
            scheduled_cleaner = self.factory.get_scheduled_cleaner()
            
            if scheduled_cleaner:
                result = scheduled_cleaner.force_cleanup()
                
                # 调用回调函数
                if self._cleanup_callback:
                    try:
                        self._cleanup_callback(result)
                    except Exception as e:
                        self.logger.error(f"清理回调函数出错: {e}")
                
                return result
            else:
                return {"status": "not_configured"}
                
        except Exception as e:
            error_msg = f"强制清理出错: {e}"
            self.logger.error(error_msg)
            return {"status": "error", "error": error_msg}
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态
        
        Returns:
            状态信息
        """
        return {
            "running": self._running,
            "check_interval_hours": self._check_interval_hours,
            "cleanup_time_hour": self._cleanup_time_hour,
            "next_cleanup_time": self._calculate_next_cleanup_time() if self._running else None,
            "thread_alive": self._scheduler_thread.is_alive() if self._scheduler_thread else False
        }


class LogCleanupService:
    """日志清理服务
    
    提供高级的日志清理服务接口。
    """
    
    def __init__(self, factory: PerformanceMonitorFactory):
        """初始化服务
        
        Args:
            factory: 性能监控器工厂
        """
        self.factory = factory
        self.scheduler = LogCleanupScheduler(factory)
        self.logger = logging.getLogger("log_cleanup_service")
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化服务
        
        Args:
            config: 配置字典
        """
        # 配置调度器
        scheduler_config = config.get("scheduler", {})
        self.scheduler.configure(scheduler_config)
        
        # 设置日志清理器
        cleanup_config = config.get("log_cleanup", {})
        if cleanup_config.get("enabled", True):
            self.factory.setup_log_cleaner(cleanup_config)
        
        self.logger.info("日志清理服务初始化完成")
    
    def start(self) -> None:
        """启动服务"""
        self.scheduler.start()
        self.logger.info("日志清理服务已启动")
    
    def stop(self) -> None:
        """停止服务"""
        self.scheduler.stop()
        self.logger.info("日志清理服务已停止")
    
    def force_cleanup(self) -> Dict[str, Any]:
        """强制执行清理
        
        Returns:
            清理结果
        """
        return self.scheduler.force_cleanup()
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态
        
        Returns:
            状态信息
        """
        status = self.scheduler.get_status()
        
        # 添加清理器状态
        cleanup_stats = self.factory.get_cleanup_stats()
        if cleanup_stats:
            status["cleanup_stats"] = cleanup_stats
        
        return status