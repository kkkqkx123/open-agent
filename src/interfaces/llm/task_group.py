"""LLM任务组管理接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple


class ITaskGroupManager(ABC):
    """任务组管理器接口"""
    
    @abstractmethod
    def get_models_for_group(self, group_reference: str) -> List[str]:
        """获取组引用对应的模型列表"""
        pass
    
    @abstractmethod
    def parse_group_reference(self, reference: str) -> Tuple[str, Optional[str]]:
        """解析组引用字符串"""
        pass
    
    @abstractmethod
    def get_fallback_groups(self, group_reference: str) -> List[str]:
        """获取降级组列表"""
        pass
    
    @abstractmethod
    def get_echelon_config(self, group_name: str, echelon_name: str) -> Optional[Dict[str, Any]]:
        """获取层级配置"""
        pass
    
    @abstractmethod
    def get_group_models_by_priority(self, group_name: str) -> List[Tuple[str, int, List[str]]]:
        """按优先级获取组的模型"""
        pass
    
    @abstractmethod
    def list_task_groups(self) -> List[str]:
        """列出所有任务组名称"""
        pass