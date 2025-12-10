"""配置处理器基类

定义配置处理器的基础接口和抽象类，提供配置处理的通用框架。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
import time
from pathlib import Path

from src.interfaces.config.processor import IConfigProcessor

logger = logging.getLogger(__name__)


class BaseConfigProcessor(IConfigProcessor):
    """配置处理器基类
    
    提供所有处理器的通用功能：
    - 统一的日志记录
    - 标准化的错误处理
    - 通用的配置遍历逻辑
    - 性能监控
    - 处理器元数据
    """
    
    def __init__(self, name: str):
        """初始化处理器
        
        Args:
            name: 处理器名称
        """
        self.name = name
        self.metadata: Dict[str, Any] = {}
        self._performance_stats: Dict[str, Any] = {}
        self._enabled = True
        
    def get_name(self) -> str:
        """获取处理器名称
        
        Returns:
            处理器名称
        """
        return self.name
    
    def set_enabled(self, enabled: bool) -> None:
        """设置处理器启用状态
        
        Args:
            enabled: 是否启用
        """
        self._enabled = enabled
        logger.debug(f"处理器 {self.name} {'启用' if enabled else '禁用'}")
    
    def is_enabled(self) -> bool:
        """检查处理器是否启用
        
        Returns:
            是否启用
        """
        return self._enabled
    
    def process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """统一的处理流程
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        if not self._enabled:
            logger.debug(f"处理器 {self.name} 已禁用，跳过处理")
            return config
        
        start_time = time.time()
        
        try:
            logger.debug(f"开始使用处理器 {self.name} 处理配置: {config_path}")
            
            # 前置处理
            config = self._pre_process(config, config_path)
            
            # 核心处理（子类实现）
            result = self._process_internal(config, config_path)
            
            # 后置处理
            result = self._post_process(result, config_path)
            
            # 记录性能
            duration = time.time() - start_time
            self._record_performance(duration)
            
            logger.debug(f"处理器 {self.name} 处理完成，耗时 {duration:.3f}s")
            return result
            
        except Exception as e:
            self._handle_error(e, config_path)
            raise
    
    def _pre_process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """前置处理（可重写）
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            前置处理后的配置数据
        """
        # 验证配置类型
        if not isinstance(config, dict):
            raise ValueError(f"配置必须是字典类型，实际类型: {type(config)}")
        
        return config
    
    def _post_process(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """后置处理（可重写）
        
        Args:
            config: 处理后的配置数据
            config_path: 配置文件路径
            
        Returns:
            后置处理后的配置数据
        """
        return config
    
    @abstractmethod
    def _process_internal(self, config: Dict[str, Any], config_path: str) -> Dict[str, Any]:
        """核心处理逻辑（子类必须实现）
        
        Args:
            config: 原始配置数据
            config_path: 配置文件路径
            
        Returns:
            处理后的配置数据
        """
        pass
    
    def _handle_error(self, error: Exception, config_path: str):
        """统一错误处理
        
        Args:
            error: 异常对象
            config_path: 配置文件路径
        """
        error_msg = f"处理器 {self.name} 处理失败 ({config_path}): {error}"
        logger.error(error_msg)
        
        # 记录错误统计
        self._performance_stats['error_count'] = self._performance_stats.get('error_count', 0) + 1
    
    def _record_performance(self, duration: float):
        """记录性能统计
        
        Args:
            duration: 处理耗时（秒）
        """
        self._performance_stats['last_duration'] = duration
        self._performance_stats['total_calls'] = self._performance_stats.get('total_calls', 0) + 1
        self._performance_stats['total_duration'] = self._performance_stats.get('total_duration', 0) + duration
        
        # 计算平均耗时
        total_calls = self._performance_stats['total_calls']
        total_duration = self._performance_stats['total_duration']
        self._performance_stats['avg_duration'] = total_duration / total_calls
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计
        
        Returns:
            性能统计数据
        """
        return self._performance_stats.copy()
    
    def reset_performance_stats(self):
        """重置性能统计"""
        self._performance_stats.clear()
        logger.debug(f"处理器 {self.name} 性能统计已重置")
    
    def set_metadata(self, key: str, value: Any):
        """设置元数据
        
        Args:
            key: 键
            value: 值
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            元数据值
        """
        return self.metadata.get(key, default)
    
    def get_all_metadata(self) -> Dict[str, Any]:
        """获取所有元数据
        
        Returns:
            所有元数据
        """
        return self.metadata.copy()
    
    def _traverse_config(self, config: Dict[str, Any], path: str = "") -> Dict[str, Any]:
        """遍历配置字典的工具方法
        
        Args:
            config: 配置字典
            path: 当前路径
            
        Returns:
            遍历结果
        """
        result = {}
        
        for key, value in config.items():
            current_path = f"{path}.{key}" if path else key
            
            if isinstance(value, dict):
                result[key] = self._traverse_config(value, current_path)
            elif isinstance(value, list):
                result[key] = [
                    self._traverse_config(item, f"{current_path}.{i}") if isinstance(item, dict) else item
                    for i, item in enumerate(value)
                ]
            else:
                result[key] = value
        
        return result
    
    def _get_config_type(self, config_path: str) -> str:
        """根据配置路径确定配置类型
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置类型
        """
        path = Path(config_path)
        parts = path.parts
        
        if "llm" in parts or "llms" in parts:
            return "llm"
        elif "workflow" in parts or "workflows" in parts:
            return "workflow"
        elif "tool" in parts or "tools" in parts:
            return "tools"
        elif "state" in parts:
            return "state"
        elif "session" in parts or "sessions" in parts:
            return "session"
        else:
            return "general"