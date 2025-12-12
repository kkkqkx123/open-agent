"""任务组配置管理器

重构后专注于任务组和轮询池的业务逻辑，配置管理委托给LLMConfigManager。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List, Tuple

from src.interfaces.llm import ITaskGroupManager
from src.core.config.config_facade import ConfigFacade

logger = get_logger(__name__)


class TaskGroupManager(ITaskGroupManager):
    """任务组配置管理器
    
    重构后专注于：
    1. 任务组和轮询池的业务逻辑
    2. 组引用解析和验证
    3. 降级策略和配置获取
    
    配置加载和管理委托给LLMConfigManager。
    """
    
    def __init__(self, config_facade: ConfigFacade):
        """
        初始化任务组管理器
        
        Args:
            config_facade: 配置门面
        """
        self._config_facade = config_facade
    
    def load_config(self) -> Any:
        """加载任务组配置
        
        委托给ConfigManager处理
        """
        # 从配置门面获取LLM配置
        llm_config = self._config_facade.get_llm_config()
        
        # 创建任务组总配置
        config_data = {
            "task_groups": llm_config.get("task_groups", {}),
            "polling_pools": llm_config.get("polling_pools", {}),
            "global_fallback": llm_config.get("global_fallback", {}),
            "concurrency_control": llm_config.get("concurrency_control", {}),
            "rate_limiting": llm_config.get("rate_limiting", {})
        }
        
        logger.info("任务组配置加载完成")
        return config_data
    
    def get_config(self) -> Any:
        """获取任务组配置"""
        return self.load_config()
    
    def get_task_group(self, name: str) -> Optional[Dict[str, Any]]:
        """获取任务组配置
        
        Args:
            name: 任务组名称
            
        Returns:
            Optional[Dict[str, Any]]: 任务组配置，如果不存在则返回None
        """
        llm_config = self._config_facade.get_llm_config()
        task_groups = llm_config.get("task_groups", {})
        return task_groups.get(name)
    
    def get_polling_pool(self, name: str) -> Optional[Dict[str, Any]]:
        """获取轮询池配置
        
        Args:
            name: 轮询池名称
            
        Returns:
            Optional[Dict[str, Any]]: 轮询池配置，如果不存在则返回None
        """
        llm_config = self._config_facade.get_llm_config()
        polling_pools = llm_config.get("polling_pools", {})
        return polling_pools.get(name)
    
    def get_echelon_config(self, group_name: str, echelon_name: str) -> Optional[Dict[str, Any]]:
        """获取层级配置
        
        Args:
            group_name: 任务组名称
            echelon_name: 层级名称
            
        Returns:
            Optional[Dict[str, Any]]: 层级配置，如果不存在则返回None
        """
        task_group = self.get_task_group(group_name)
        if not task_group:
            return None
        
        echelons = task_group.get("echelons", {})
        return echelons.get(echelon_name)
    
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
            List[str]: 模型名称列表
        """
        group_name, echelon_or_task = self.parse_group_reference(group_reference)
        
        if not group_name:
            return []
        
        task_group = self.get_task_group(group_name)
        if not task_group:
            return []
        
        if echelon_or_task:
            echelon_config = self.get_echelon_config(group_name, echelon_or_task)
            if echelon_config:
                return echelon_config.get("models", [])
        else:
            # 如果没有指定层级，返回所有层级的模型
            all_models = []
            echelons = task_group.get("echelons", {})
            for echelon_config in echelons.values():
                all_models.extend(echelon_config.get("models", []))
            return all_models
        
        return []
    
    def get_fallback_groups(self, group_reference: str) -> List[str]:
        """
        获取降级组列表
        
        Args:
            group_reference: 组引用，如 "fast_group.echelon1"
            
        Returns:
            List[str]: 降级组引用列表
        """
        group_name, echelon_or_task = self.parse_group_reference(group_reference)
        
        if not group_name:
            return []
        
        task_group = self.get_task_group(group_name)
        if not task_group:
            return []
        
        # 优先使用任务组特定的降级配置
        fallback_config = task_group.get("fallback_config")
        if fallback_config:
            return fallback_config.get("fallback_groups", [])
        
        fallback_groups = []
        
        # 根据降级策略生成降级组
        fallback_strategy = task_group.get("fallback_strategy", "echelon_down")
        if fallback_strategy == "echelon_down":
            if echelon_or_task and echelon_or_task.startswith("echelon"):
                # 获取下一层级
                echelon_num = int(echelon_or_task.replace("echelon", ""))
                next_echelon = f"echelon{echelon_num + 1}"
                next_echelon_config = self.get_echelon_config(group_name, next_echelon)
                if next_echelon_config:
                    fallback_groups.append(f"{group_name}.{next_echelon}")
        
        # 可以添加更多降级策略的实现
        
        return fallback_groups
    
    def get_fallback_config(self, group_name: str) -> Dict[str, Any]:
        """
        获取任务组的降级配置
        
        Args:
            group_name: 任务组名称
            
        Returns:
            Dict[str, Any]: 降级配置字典
        """
        task_group = self.get_task_group(group_name)
        if not task_group:
            return {}
        
        fallback_config = task_group.get("fallback_config")
        if fallback_config:
            return {
                "strategy": fallback_config.get("strategy", "echelon_down"),
                "fallback_groups": fallback_config.get("fallback_groups", []),
                "max_attempts": fallback_config.get("max_attempts", 3),
                "retry_delay": fallback_config.get("retry_delay", 1.0),
                "circuit_breaker": {
                    "failure_threshold": fallback_config.get("circuit_breaker", {}).get("failure_threshold", 5),
                    "recovery_time": fallback_config.get("circuit_breaker", {}).get("recovery_time", 60),
                    "half_open_requests": fallback_config.get("circuit_breaker", {}).get("half_open_requests", 1)
                } if fallback_config.get("circuit_breaker") else None
            }
        
        # 返回默认配置
        return {
            "strategy": task_group.get("fallback_strategy", "echelon_down"),
            "fallback_groups": self.get_fallback_groups(f"{group_name}.echelon1"),
            "max_attempts": 3,
            "retry_delay": 1.0,
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_time": 60,
                "half_open_requests": 1
            }
        }
    
    def get_polling_pool_fallback_config(self, pool_name: str) -> Dict[str, Any]:
        """
        获取轮询池的降级配置
        
        Args:
            pool_name: 轮询池名称
            
        Returns:
            Dict[str, Any]: 降级配置字典
        """
        polling_pool = self.get_polling_pool(pool_name)
        if not polling_pool:
            return {}
        
        fallback_config = polling_pool.get("fallback_config")
        if fallback_config:
            return {
                "strategy": fallback_config.get("strategy", "instance_rotation"),
                "max_instance_attempts": fallback_config.get("max_instance_attempts", 2)
            }
        
        # 返回默认配置
        return {
            "strategy": "instance_rotation",
            "max_instance_attempts": 2
        }
    
    def validate_group_reference(self, reference: str) -> bool:
        """
        验证组引用是否有效
        
        Args:
            reference: 组引用
            
        Returns:
            bool: 是否有效
        """
        group_name, echelon_or_task = self.parse_group_reference(reference)
        
        if not group_name:
            return False
        
        task_group = self.get_task_group(group_name)
        if not task_group:
            return False
        
        if echelon_or_task:
            echelon_config = self.get_echelon_config(group_name, echelon_or_task)
            return echelon_config is not None
        
        return True
    
    def list_task_groups(self) -> List[str]:
        """列出所有任务组名称
        
        Returns:
            List[str]: 任务组名称列表
        """
        llm_config = self._config_facade.get_llm_config()
        task_groups = llm_config.get("task_groups", {})
        return list(task_groups.keys())
    
    def list_polling_pools(self) -> List[str]:
        """列出所有轮询池名称
        
        Returns:
            List[str]: 轮询池名称列表
        """
        llm_config = self._config_facade.get_llm_config()
        polling_pools = llm_config.get("polling_pools", {})
        return list(polling_pools.keys())
    
    def get_group_models_by_priority(self, group_name: str) -> List[Tuple[str, int, List[str]]]:
        """
        按优先级获取组的模型
        
        Args:
            group_name: 组名称
            
        Returns:
            List[Tuple[str, int, List[str]]]: [(echelon_name, priority, models), ...] 按优先级排序
        """
        task_group = self.get_task_group(group_name)
        if not task_group:
            return []
        
        echelon_list = []
        echelons = task_group.get("echelons", {})
        for echelon_name, echelon_config in echelons.items():
            echelon_list.append((
                echelon_name, 
                echelon_config.get("priority", 999), 
                echelon_config.get("models", [])
            ))
        
        # 按优先级排序（数字越小优先级越高）
        echelon_list.sort(key=lambda x: x[1])
        
        return echelon_list
    
    def get_global_fallback_config(self) -> Dict[str, Any]:
        """获取全局降级配置
        
        Returns:
            Dict[str, Any]: 全局降级配置
        """
        llm_config = self._config_facade.get_llm_config()
        return llm_config.get("global_fallback", {})
    
    def reload_config(self) -> Any:
        """重新加载配置
        
        委托给LLMConfigManager处理
        """
        self._config_facade.reload_config("llm")
        return self.load_config()
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态
        
        委托给ConfigManager处理
        
        Returns:
            Dict[str, Any]: 配置状态信息
        """
        # 返回配置状态信息
        llm_config = self._config_facade.get_llm_config()
        return {
            "loaded": True,
            "task_groups_count": len(llm_config.get("task_groups", {})),
            "polling_pools_count": len(llm_config.get("polling_pools", {})),
            "has_global_fallback": len(llm_config.get("global_fallback", {})) > 0,
            "has_concurrency_control": len(llm_config.get("concurrency_control", {})) > 0,
            "has_rate_limiting": len(llm_config.get("rate_limiting", {})) > 0
        }