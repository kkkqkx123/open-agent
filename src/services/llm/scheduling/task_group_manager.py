"""任务组配置管理器"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from src.core.llm.interfaces import ITaskGroupManager

logger = logging.getLogger(__name__)


class TaskGroupManager(ITaskGroupManager):
    """任务组配置管理器"""
    
    def __init__(self, config_loader):
        """
        初始化任务组管理器
        
        Args:
            config_loader: 配置加载器
        """
        self.config_loader = config_loader
        self._task_groups_config: Optional[Any] = None
        self._config_base_path = "llms"
    
    def load_config(self) -> Any:
        """加载任务组配置"""
        try:
            # 加载任务组配置
            task_groups = self._load_task_groups()
            
            # 加载轮询池配置
            polling_pools = self._load_polling_pools()
            
            # 加载全局配置
            global_fallback = self._load_global_fallback()
            concurrency_control = self._load_concurrency_control()
            rate_limiting = self._load_rate_limiting()
            
            # 创建任务组总配置
            config_data = {
                "task_groups": task_groups,
                "polling_pools": polling_pools,
                "global_fallback": global_fallback,
                "concurrency_control": concurrency_control,
                "rate_limiting": rate_limiting
            }
            
            # 创建配置对象（临时实现，将在更新导入路径时修复）
            self._task_groups_config = config_data
            logger.info("任务组配置加载成功")
            return self._task_groups_config
        except Exception as e:
            logger.error(f"任务组配置加载失败: {e}")
            # from .exceptions import LLMConfigurationError
            # raise LLMConfigurationError(f"任务组配置加载失败: {e}")
            raise Exception(f"任务组配置加载失败: {e}")
    
    def get_config(self) -> Any:
        """获取任务组配置"""
        if self._task_groups_config is None:
            self._task_groups_config = self.load_config()
        return self._task_groups_config
    
    def get_task_group(self, name: str) -> Optional[Dict[str, Any]]:
        """获取任务组配置"""
        config = self.get_config()
        return config.get("task_groups", {}).get(name)
    
    def get_polling_pool(self, name: str) -> Optional[Dict[str, Any]]:
        """获取轮询池配置"""
        config = self.get_config()
        return config.get("polling_pools", {}).get(name)
    
    def get_echelon_config(self, group_name: str, echelon_name: str) -> Optional[Dict[str, Any]]:
        """获取层级配置"""
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
            模型名称列表
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
            降级组引用列表
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
            降级配置字典
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
            降级配置字典
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
            是否有效
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
        """列出所有任务组名称"""
        config = self.get_config()
        return list(config.get("task_groups", {}).keys())
    
    def list_polling_pools(self) -> List[str]:
        """列出所有轮询池名称"""
        config = self.get_config()
        return list(config.get("polling_pools", {}).keys())
    
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
        """获取全局降级配置"""
        config = self.get_config()
        return config.get("global_fallback", {})
    
    def reload_config(self) -> Any:
        """重新加载配置"""
        self._task_groups_config = None
        return self.load_config()
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        config = self.get_config()
        
        return {
            "config_loaded": True,
            "task_groups_count": len(config.get("task_groups", {})),
            "polling_pools_count": len(config.get("polling_pools", {})),
            "task_groups": list(config.get("task_groups", {}).keys()),
            "polling_pools": list(config.get("polling_pools", {}).keys()),
            "global_fallback_enabled": config.get("global_fallback", {}).get("enabled", False),
            "concurrency_control_enabled": config.get("concurrency_control", {}).get("enabled", False),
            "rate_limiting_enabled": config.get("rate_limiting", {}).get("enabled", False)
        }
    
    def _load_task_groups(self) -> Dict[str, Any]:
        """加载所有任务组配置"""
        task_groups = {}
        
        # 首先加载注册表配置
        try:
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self.config_loader.load(registry_path)
            
            # 从注册表获取任务组配置文件列表
            task_groups_registry = registry_config.get("task_groups", {})
            
            # 加载每个启用的任务组配置
            for group_name, group_info in task_groups_registry.items():
                if not group_info.get("enabled", True):
                    logger.debug(f"任务组 {group_name} 已禁用，跳过加载")
                    continue
                
                group_file = group_info.get("file")
                if not group_file:
                    logger.warning(f"任务组 {group_name} 缺少文件路径配置")
                    continue
                
                try:
                    config_path = f"{self._config_base_path}/{group_file}"
                    group_config = self.config_loader.load(config_path)
                    
                    # 验证配置中的名称是否与注册表中的名称一致
                    config_name = group_config.get("name")
                    if config_name and config_name != group_name:
                        logger.warning(f"任务组配置文件中的名称 '{config_name}' 与注册表中的名称 '{group_name}' 不匹配")
                    
                    task_groups[group_name] = group_config
                    logger.debug(f"成功加载任务组配置: {group_name}")
                    
                except Exception as e:
                    logger.warning(f"加载任务组配置失败 {group_name} ({group_file}): {e}")
                    
        except Exception as e:
            logger.error(f"加载任务组注册表失败: {e}")
            # 如果注册表加载失败，使用默认的任务组列表作为后备
            return self._load_default_task_groups()
        
        return task_groups
    
    def _load_default_task_groups(self) -> Dict[str, Any]:
        """加载默认任务组配置（后备方案）"""
        task_groups = {}
        
        # 默认任务组配置文件路径
        default_group_files = [
            "groups/fast_group.yaml",
            "groups/plan_group.yaml",
            "groups/thinking_group.yaml",
            "groups/execute_group.yaml",
            "groups/review_group.yaml",
            "groups/high_payload_group.yaml",
            "groups/fast_small_group.yaml"
        ]
        
        # 加载每个任务组配置
        for group_file in default_group_files:
            try:
                config_path = f"{self._config_base_path}/{group_file}"
                group_config = self.config_loader.load(config_path)
                group_name = group_config.get("name")
                if group_name:
                    task_groups[group_name] = group_config
                    logger.debug(f"使用默认配置加载任务组: {group_name}")
            except Exception as e:
                logger.warning(f"加载默认任务组配置失败 {group_file}: {e}")
        
        return task_groups
    
    def _load_polling_pools(self) -> Dict[str, Any]:
        """加载所有轮询池配置"""
        polling_pools = {}
        
        # 首先加载注册表配置
        try:
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self.config_loader.load(registry_path)
            
            # 从注册表获取轮询池配置文件列表
            polling_pools_registry = registry_config.get("polling_pools", {})
            
            # 加载每个启用的轮询池配置
            for pool_name, pool_info in polling_pools_registry.items():
                if not pool_info.get("enabled", True):
                    logger.debug(f"轮询池 {pool_name} 已禁用，跳过加载")
                    continue
                
                pool_file = pool_info.get("file")
                if not pool_file:
                    logger.warning(f"轮询池 {pool_name} 缺少文件路径配置")
                    continue
                
                try:
                    config_path = f"{self._config_base_path}/{pool_file}"
                    pool_config = self.config_loader.load(config_path)
                    
                    # 验证配置中的名称是否与注册表中的名称一致
                    config_name = pool_config.get("name")
                    if config_name and config_name != pool_name:
                        logger.warning(f"轮询池配置文件中的名称 '{config_name}' 与注册表中的名称 '{pool_name}' 不匹配")
                    
                    polling_pools[pool_name] = pool_config
                    logger.debug(f"成功加载轮询池配置: {pool_name}")
                    
                except Exception as e:
                    logger.warning(f"加载轮询池配置失败 {pool_name} ({pool_file}): {e}")
                    
        except Exception as e:
            logger.error(f"加载轮询池注册表失败: {e}")
            # 如果注册表加载失败，使用默认的轮询池列表作为后备
            return self._load_default_polling_pools()
        
        return polling_pools
    
    def _load_default_polling_pools(self) -> Dict[str, Any]:
        """加载默认轮询池配置（后备方案）"""
        polling_pools = {}
        
        # 默认轮询池配置文件路径
        default_pool_files = [
            "polling_pools/single_turn_pool.yaml",
            "polling_pools/multi_turn_pool.yaml",
            "polling_pools/high_concurrency_pool.yaml"
        ]
        
        # 加载每个轮询池配置
        for pool_file in default_pool_files:
            try:
                config_path = f"{self._config_base_path}/{pool_file}"
                pool_config = self.config_loader.load(config_path)
                pool_name = pool_config.get("name")
                if pool_name:
                    polling_pools[pool_name] = pool_config
                    logger.debug(f"使用默认配置加载轮询池: {pool_name}")
            except Exception as e:
                logger.warning(f"加载默认轮询池配置失败 {pool_file}: {e}")
        
        return polling_pools
    
    def _load_global_fallback(self) -> Dict[str, Any]:
        """加载全局降级配置"""
        # 首先尝试从注册表加载
        try:
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self.config_loader.load(registry_path)
            
            # 从注册表获取全局配置文件列表
            global_configs = registry_config.get("global_configs", {})
            global_fallback_info = global_configs.get("global_fallback", {})
            
            if not global_fallback_info.get("enabled", True):
                logger.debug("全局降级配置已禁用")
                return {}
            
            fallback_file = global_fallback_info.get("file")
            if fallback_file:
                config_path = f"{self._config_base_path}/{fallback_file}"
                config = self.config_loader.load(config_path)
                logger.debug("从注册表成功加载全局降级配置")
                return config
                
        except Exception as e:
            logger.warning(f"从注册表加载全局降级配置失败: {e}")
        
        # 如果注册表加载失败，直接加载默认文件
        try:
            config_path = f"{self._config_base_path}/global_fallback.yaml"
            config = self.config_loader.load(config_path)
            logger.debug("使用默认路径加载全局降级配置")
            return config
        except Exception as e:
            logger.warning(f"加载全局降级配置失败: {e}")
            return {}  # 返回默认配置
    
    def _load_concurrency_control(self) -> Dict[str, Any]:
        """加载并发控制配置"""
        # 首先尝试从注册表加载
        try:
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self.config_loader.load(registry_path)
            
            # 从注册表获取全局配置文件列表
            global_configs = registry_config.get("global_configs", {})
            concurrency_control_info = global_configs.get("concurrency_control", {})
            
            if not concurrency_control_info.get("enabled", True):
                logger.debug("并发控制配置已禁用")
                return {}
            
            concurrency_file = concurrency_control_info.get("file")
            if concurrency_file:
                config_path = f"{self._config_base_path}/{concurrency_file}"
                config = self.config_loader.load(config_path)
                logger.debug("从注册表成功加载并发控制配置")
                return config
                
        except Exception as e:
            logger.warning(f"从注册表加载并发控制配置失败: {e}")
        
        # 如果注册表加载失败，直接加载默认文件
        try:
            config_path = f"{self._config_base_path}/concurrency_control.yaml"
            config = self.config_loader.load(config_path)
            logger.debug("使用默认路径加载并发控制配置")
            return config
        except Exception as e:
            logger.warning(f"加载并发控制配置失败: {e}")
            return {}  # 返回默认配置
    
    def _load_rate_limiting(self) -> Dict[str, Any]:
        """加载速率限制配置"""
        # 首先尝试从注册表加载
        try:
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self.config_loader.load(registry_path)
            
            # 从注册表获取全局配置文件列表
            global_configs = registry_config.get("global_configs", {})
            rate_limiting_info = global_configs.get("rate_limiting", {})
            
            if not rate_limiting_info.get("enabled", True):
                logger.debug("速率限制配置已禁用")
                return {}
            
            rate_limiting_file = rate_limiting_info.get("file")
            if rate_limiting_file:
                config_path = f"{self._config_base_path}/{rate_limiting_file}"
                config = self.config_loader.load(config_path)
                logger.debug("从注册表成功加载速率限制配置")
                return config
                
        except Exception as e:
            logger.warning(f"从注册表加载速率限制配置失败: {e}")
        
        # 如果注册表加载失败，直接加载默认文件
        try:
            config_path = f"{self._config_base_path}/rate_limiting.yaml"
            config = self.config_loader.load(config_path)
            logger.debug("使用默认路径加载速率限制配置")
            return config
        except Exception as e:
            logger.warning(f"加载速率限制配置失败: {e}")
            return {}  # 返回默认配置