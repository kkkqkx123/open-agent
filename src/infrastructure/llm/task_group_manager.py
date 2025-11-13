"""任务组配置管理器"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from ..config_interfaces import IConfigLoader
from ..config.models.task_group_config import (
    TaskGroupsConfig, TaskGroupConfig, PollingPoolConfig, 
    EchelonConfig, GlobalFallbackConfig
)
from .exceptions import LLMConfigurationError

logger = logging.getLogger(__name__)


class TaskGroupManager:
    """任务组配置管理器"""
    
    def __init__(self, config_loader: IConfigLoader):
        """
        初始化任务组管理器
        
        Args:
            config_loader: 配置加载器
        """
        self.config_loader = config_loader
        self._task_groups_config: Optional[TaskGroupsConfig] = None
        self._config_path = "llms/groups/_task_groups.yaml"
    
    def load_config(self) -> TaskGroupsConfig:
        """加载任务组配置"""
        try:
            config_data = self.config_loader.load(self._config_path)
            self._task_groups_config = TaskGroupsConfig.from_dict(config_data)
            logger.info("任务组配置加载成功")
            return self._task_groups_config
        except Exception as e:
            logger.error(f"任务组配置加载失败: {e}")
            raise LLMConfigurationError(f"任务组配置加载失败: {e}")
    
    def get_config(self) -> TaskGroupsConfig:
        """获取任务组配置"""
        if self._task_groups_config is None:
            self.load_config()
        return self._task_groups_config
    
    def get_task_group(self, name: str) -> Optional[TaskGroupConfig]:
        """获取任务组配置"""
        config = self.get_config()
        return config.get_task_group(name)
    
    def get_polling_pool(self, name: str) -> Optional[PollingPoolConfig]:
        """获取轮询池配置"""
        config = self.get_config()
        return config.get_polling_pool(name)
    
    def get_echelon_config(self, group_name: str, echelon_name: str) -> Optional[EchelonConfig]:
        """获取层级配置"""
        config = self.get_config()
        return config.get_echelon_config(group_name, echelon_name)
    
    def parse_group_reference(self, reference: str) -> Tuple[str, Optional[str]]:
        """
        解析组引用字符串
        
        Args:
            reference: 组引用，如 "fast_group.echelon1" 或 "fast_small_group.translation"
            
        Returns:
            (group_name, echelon_or_task_name)
        """
        parts = reference.split(".", 1)
        group_name = parts[0]
        echelon_or_task = parts[1] if len(parts) > 1 else None
        return group_name, echelon_or_task
    
    def get_models_for_group(self, group_reference: str) -> List[str]:
        """
        获取组引用对应的模型列表
        
        Args:
            group_reference: 组引用，如 "fast_group.echelon1"
            
        Returns:
            模型名称列表
        """
        group_name, echelon_or_task = self.parse_group_reference(group_reference)
        
        if not group_name:
            return []
        
        task_group = self.get_task_group(group_name)
        if not task_group:
            return []
        
        if echelon_or_task:
            echelon_config = task_group.echelons.get(echelon_or_task)
            if echelon_config:
                return echelon_config.models
        else:
            # 如果没有指定层级，返回所有层级的模型
            all_models = []
            for echelon_config in task_group.echelons.values():
                all_models.extend(echelon_config.models)
            return all_models
        
        return []
    
    def get_fallback_groups(self, group_reference: str) -> List[str]:
        """
        获取降级组列表
        
        Args:
            group_reference: 组引用，如 "fast_group.echelon1"
            
        Returns:
            降级组引用列表
        """
        group_name, echelon_or_task = self.parse_group_reference(group_reference)
        
        if not group_name:
            return []
        
        task_group = self.get_task_group(group_name)
        if not task_group:
            return []
        
        fallback_groups = []
        
        # 根据降级策略生成降级组
        if task_group.fallback_strategy.value == "echelon_down":
            if echelon_or_task and echelon_or_task.startswith("echelon"):
                # 获取下一层级
                echelon_num = int(echelon_or_task.replace("echelon", ""))
                next_echelon = f"echelon{echelon_num + 1}"
                if next_echelon in task_group.echelons:
                    fallback_groups.append(f"{group_name}.{next_echelon}")
        
        # 可以添加更多降级策略的实现
        
        return fallback_groups
    
    def validate_group_reference(self, reference: str) -> bool:
        """
        验证组引用是否有效
        
        Args:
            reference: 组引用
            
        Returns:
            是否有效
        """
        group_name, echelon_or_task = self.parse_group_reference(reference)
        
        if not group_name:
            return False
        
        task_group = self.get_task_group(group_name)
        if not task_group:
            return False
        
        if echelon_or_task:
            return echelon_or_task in task_group.echelons
        
        return True
    
    def list_task_groups(self) -> List[str]:
        """列出所有任务组名称"""
        config = self.get_config()
        return list(config.task_groups.keys())
    
    def list_polling_pools(self) -> List[str]:
        """列出所有轮询池名称"""
        config = self.get_config()
        return list(config.polling_pools.keys())
    
    def get_group_models_by_priority(self, group_name: str) -> List[Tuple[str, int, List[str]]]:
        """
        按优先级获取组的模型
        
        Args:
            group_name: 组名称
            
        Returns:
            [(echelon_name, priority, models), ...] 按优先级排序
        """
        task_group = self.get_task_group(group_name)
        if not task_group:
            return []
        
        echelon_list = []
        for echelon_name, echelon_config in task_group.echelons.items():
            echelon_list.append((echelon_name, echelon_config.priority, echelon_config.models))
        
        # 按优先级排序（数字越小优先级越高）
        echelon_list.sort(key=lambda x: x[1])
        
        return echelon_list
    
    def get_global_fallback_config(self) -> GlobalFallbackConfig:
        """获取全局降级配置"""
        config = self.get_config()
        return config.global_fallback
    
    def reload_config(self) -> TaskGroupsConfig:
        """重新加载配置"""
        self._task_groups_config = None
        return self.load_config()
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        config = self.get_config()
        
        return {
            "config_loaded": True,
            "task_groups_count": len(config.task_groups),
            "polling_pools_count": len(config.polling_pools),
            "task_groups": list(config.task_groups.keys()),
            "polling_pools": list(config.polling_pools.keys()),
            "global_fallback_enabled": config.global_fallback.enabled,
            "concurrency_control_enabled": config.concurrency_control.enabled,
            "rate_limiting_enabled": config.rate_limiting.enabled
        }