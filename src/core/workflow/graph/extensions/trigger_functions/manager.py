"""触发器函数管理器

提供统一的触发器函数管理接口。
"""

from typing import Dict, Any, Callable, Optional, List
from src.interfaces.dependency_injection import get_logger

from .loader import TriggerFunctionLoader
from .builtin import BuiltinTriggerFunctions
from .config import TriggerCompositionConfig
from src.core.workflow.registry import TriggerRegistry, TriggerConfig

logger = get_logger(__name__)


class TriggerFunctionManager:
    """触发器函数管理器
    
    提供统一的触发器函数管理接口，是系统的入口点。
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化触发器函数管理器
        
        Args:
            config_dir: 配置目录路径
        """
        self.registry = TriggerRegistry()
        self.loader = TriggerFunctionLoader(self.registry)
        
        # 注册内置函数
        self._register_rest_functions()
        
        # 从配置目录加载
        if config_dir:
            self.loader.load_from_config_directory(config_dir)
    
    def _register_rest_functions(self) -> None:
        """注册内置函数"""
        rest_evaluate_functions = BuiltinTriggerFunctions.get_all_evaluate_functions()
        rest_execute_functions = BuiltinTriggerFunctions.get_all_execute_functions()
        
        # 注册评估函数
        for name, func in rest_evaluate_functions.items():
            # 创建配置
            config = TriggerConfig(
                name=name,
                trigger_type="evaluate",
                description=f"内置评估函数: {name}"
            )
            
            self.registry.register_trigger(name, func, config, is_builtin=True)
        
        # 注册执行函数
        for name, func in rest_execute_functions.items():
            # 创建配置
            config = TriggerConfig(
                name=name,
                trigger_type="execute",
                description=f"内置执行函数: {name}"
            )
            
            self.registry.register_trigger(name, func, config, is_builtin=True)
        
        # 注册到加载器
        all_rest_functions = BuiltinTriggerFunctions.get_all_functions()
        self.loader.register_rest_functions(all_rest_functions)
    
    def get_evaluate_function(self, name: str) -> Optional[Callable]:
        """获取评估函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 评估函数，如果不存在返回None
        """
        return self.registry.get_trigger(name)
    
    def get_execute_function(self, name: str) -> Optional[Callable]:
        """获取执行函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 执行函数，如果不存在返回None
        """
        return self.registry.get_trigger(name)
    
    def get_function(self, name: str) -> Optional[Callable]:
        """获取函数（通用）
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 函数，如果不存在返回None
        """
        return self.registry.get_trigger(name)
    
    def list_evaluate_functions(self) -> List[str]:
        """列出评估函数
        
        Returns:
            List[str]: 评估函数名称列表
        """
        return self.registry.list_triggers_by_type("evaluate")
    
    def list_execute_functions(self) -> List[str]:
        """列出执行函数
        
        Returns:
            List[str]: 执行函数名称列表
        """
        return self.registry.list_triggers_by_type("execute")
    
    def list_functions(self, function_type: Optional[str] = None) -> List[str]:
        """列出函数
        
        Args:
            function_type: 函数类型过滤器，如果为None则返回所有函数
            
        Returns:
            List[str]: 函数名称列表
        """
        return self.registry.list_triggers_by_type(function_type) if function_type else self.registry.list_triggers()
    
    def get_function_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取函数信息
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Dict[str, Any]]: 函数信息，如果不存在返回None
        """
        config = self.registry.get_trigger_config(name)
        if not config:
            return None
        
        return {
            "name": config.name,
            "description": config.description,
            "trigger_type": config.trigger_type,
            "is_async": config.is_async,
            "category": config.category
        }
    
    def validate_function(self, name: str, parameters: Dict[str, Any]) -> List[str]:
        """验证函数参数
        
        Args:
            name: 函数名称
            parameters: 参数字典
            
        Returns:
            List[str]: 验证错误列表
        """
        return self.registry.validate_trigger_config(name, parameters)
    
    def register_custom_function(
        self, 
        name: str, 
        function: Callable, 
        config: Optional[TriggerConfig] = None
    ) -> None:
        """注册自定义函数
        
        Args:
            name: 函数名称
            function: 函数对象
            config: 函数配置，如果为None则创建默认配置
        """
        if config is None:
            config = TriggerConfig(
                name=name,
                trigger_type="custom",
                description=f"自定义函数: {name}"
            )
        
        self.registry.register_trigger(name, function, config)
    
    def unregister_function(self, name: str) -> bool:
        """注销函数
        
        Args:
            name: 函数名称
            
        Returns:
            bool: 是否成功注销
        """
        return self.registry.unregister_trigger(name)
    
    def register_composition(self, config: TriggerCompositionConfig) -> None:
        """注册触发器组合
        
        Args:
            config: 触发器组合配置
        """
        self.registry.register_composition(config.name, config.__dict__)
    
    def get_composition(self, name: str) -> Optional[TriggerCompositionConfig]:
        """获取触发器组合
        
        Args:
            name: 组合名称
            
        Returns:
            Optional[TriggerCompositionConfig]: 触发器组合配置，如果不存在返回None
        """
        composition = self.registry.get_composition(name)
        if composition:
            # 重新创建 TriggerCompositionConfig 对象
            from .config import TriggerCompositionConfig
            return TriggerCompositionConfig(**composition)
        return None
    
    def list_compositions(self) -> List[str]:
        """列出所有触发器组合
        
        Returns:
            List[str]: 触发器组合名称列表
        """
        return self.registry.list_compositions()
    
    def get_function_types(self) -> List[str]:
        """获取所有函数类型
        
        Returns:
            List[str]: 函数类型列表
        """
        return self.registry.get_trigger_types()
    
    def get_functions_by_type(self, function_type: str) -> List[str]:
        """获取指定类型的函数
        
        Args:
            function_type: 函数类型
            
        Returns:
            List[str]: 函数名称列表
        """
        return self.registry.list_triggers_by_type(function_type)
    
    def reload_from_config(self, config_dir: str) -> None:
        """从配置目录重新加载函数
        
        Args:
            config_dir: 配置目录路径
        """
        # 清除现有的配置函数（保留内置函数）
        rest_functions = self.registry.list_triggers_by_type("evaluate") + \
                           self.registry.list_triggers_by_type("execute")
        custom_functions = [name for name in self.registry.list_triggers()
                           if name not in rest_functions]
        
        for func_name in custom_functions:
            self.registry.unregister_trigger(func_name)
        
        # 重新加载配置
        self.loader.load_from_config_directory(config_dir)
    
    def validate_all_functions(self) -> Dict[str, List[str]]:
        """验证所有注册的函数
        
        Returns:
            Dict[str, List[str]]: 验证结果，键为函数名称，值为错误列表
        """
        results = {}
        
        for func_name in self.registry.list_triggers():
            config = self.registry.get_trigger_config(func_name)
            if config:
                errors = []
                
                # 验证配置
                if not config.name:
                    errors.append("函数名称不能为空")
                
                if not config.trigger_type:
                    errors.append("函数类型不能为空")
                
                if errors:
                    results[func_name] = errors
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "total_functions": self.registry.size(),
            "total_compositions": len(self.registry.list_compositions()),
            "function_types": {},
            "builtin_functions": len(self.registry.get_builtin_triggers()),
            "custom_functions": len(self.registry.get_custom_triggers())
        }
        
        # 按类型统计
        for func_type in self.registry.get_trigger_types():
            functions = self.registry.list_triggers_by_type(func_type)
            stats["function_types"][func_type] = len(functions)
        
        return stats
    
    def create_trigger_from_composition(self, composition_name: str, trigger_id: str, config: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """从组合创建触发器
        
        Args:
            composition_name: 组合名称
            trigger_id: 触发器ID
            config: 触发器配置，如果为None则使用默认配置
            
        Returns:
            Optional[Any]: 触发器实例，如果创建失败返回None
        """
        composition = self.get_composition(composition_name)
        if not composition:
            logger.error(f"触发器组合不存在: {composition_name}")
            return None
        
        # 获取评估函数和执行函数
        evaluate_func = self.registry.get_trigger(composition.evaluate_function.name)
        execute_func = self.registry.get_trigger(composition.execute_function.name)
        
        if not evaluate_func or not execute_func:
            logger.error(f"组合中的函数不存在: {composition_name}")
            return None
        
        # 合并配置
        trigger_config = composition.default_config.copy()
        if config:
            trigger_config.update(config)
        
        # 创建触发器
        try:
            from ...extensions.triggers.builtin_triggers import CustomTrigger
            
            return CustomTrigger(
                trigger_id=trigger_id,
                evaluate_func=evaluate_func,
                execute_func=execute_func,
                config=trigger_config
            )
        except Exception as e:
            logger.error(f"创建触发器失败: {e}")
            return None
 

# 全局触发器函数管理器实例
_global_manager: Optional[TriggerFunctionManager] = None


def get_trigger_function_manager(config_dir: Optional[str] = None) -> TriggerFunctionManager:
    """获取全局触发器函数管理器实例
    
    Args:
        config_dir: 配置目录路径，只在第一次调用时有效
        
    Returns:
        TriggerFunctionManager: 触发器函数管理器实例
    """
    global _global_manager
    
    if _global_manager is None:
        _global_manager = TriggerFunctionManager(config_dir)
    
    return _global_manager


def reset_trigger_function_manager() -> None:
    """重置全局触发器函数管理器实例"""
    global _global_manager
    _global_manager = None