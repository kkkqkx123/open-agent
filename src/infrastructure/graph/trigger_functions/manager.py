"""触发器函数管理器

提供统一的触发器函数管理接口。
"""

from typing import Dict, Any, Callable, Optional, List
import logging

from .registry import TriggerFunctionRegistry, TriggerFunctionConfig
from .loader import TriggerFunctionLoader
from .rest import BuiltinTriggerFunctions
from .config import TriggerCompositionConfig

logger = logging.getLogger(__name__)


class TriggerFunctionManager:
    """触发器函数管理器
    
    提供统一的触发器函数管理接口，是系统的入口点。
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化触发器函数管理器
        
        Args:
            config_dir: 配置目录路径
        """
        self.registry = TriggerFunctionRegistry()
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
            config = TriggerFunctionConfig(
                name=name,
                description=f"内置评估函数: {name}",
                function_type="evaluate",
                parameters={},
                implementation="rest",
                metadata={},
                dependencies=[],
                return_schema={"type": "boolean"},
                input_schema={
                    "type": "object",
                    "properties": {
                        "state": {"type": "object"},
                        "context": {"type": "object"}
                    }
                }
            )
            
            self.registry.register_function(name, func, config, is_rest=True)
        
        # 注册执行函数
        for name, func in rest_execute_functions.items():
            # 创建配置
            config = TriggerFunctionConfig(
                name=name,
                description=f"内置执行函数: {name}",
                function_type="execute",
                parameters={},
                implementation="rest",
                metadata={},
                dependencies=[],
                return_schema={"type": "object"},
                input_schema={
                    "type": "object",
                    "properties": {
                        "state": {"type": "object"},
                        "context": {"type": "object"}
                    }
                }
            )
            
            self.registry.register_function(name, func, config, is_rest=True)
        
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
        return self.registry.get_function(name)
    
    def get_execute_function(self, name: str) -> Optional[Callable]:
        """获取执行函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 执行函数，如果不存在返回None
        """
        return self.registry.get_function(name)
    
    def get_function(self, name: str) -> Optional[Callable]:
        """获取函数（通用）
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 函数，如果不存在返回None
        """
        return self.registry.get_function(name)
    
    def list_evaluate_functions(self) -> List[str]:
        """列出评估函数
        
        Returns:
            List[str]: 评估函数名称列表
        """
        return self.registry.list_functions_by_type("evaluate")
    
    def list_execute_functions(self) -> List[str]:
        """列出执行函数
        
        Returns:
            List[str]: 执行函数名称列表
        """
        return self.registry.list_functions_by_type("execute")
    
    def list_functions(self, function_type: Optional[str] = None) -> List[str]:
        """列出函数
        
        Args:
            function_type: 函数类型过滤器，如果为None则返回所有函数
            
        Returns:
            List[str]: 函数名称列表
        """
        return self.registry.list_functions_by_type(function_type) if function_type else self.registry.list_functions()
    
    def get_function_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取函数信息
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Dict[str, Any]]: 函数信息，如果不存在返回None
        """
        config = self.registry.get_function_config(name)
        if not config:
            return None
        
        return {
            "name": config.name,
            "description": config.description,
            "function_type": config.function_type,
            "parameters": config.parameters,
            "implementation": config.implementation,
            "metadata": config.metadata,
            "dependencies": config.dependencies,
            "return_schema": config.return_schema,
            "input_schema": config.input_schema
        }
    
    def validate_function(self, name: str, parameters: Dict[str, Any]) -> List[str]:
        """验证函数参数
        
        Args:
            name: 函数名称
            parameters: 参数字典
            
        Returns:
            List[str]: 验证错误列表
        """
        config = self.registry.get_function_config(name)
        if not config:
            return [f"函数不存在: {name}"]
        
        errors = []
        input_schema = config.input_schema
        
        # 简单的参数验证
        if isinstance(input_schema, dict) and "properties" in input_schema:
            required = input_schema.get("required", [])
            properties = input_schema.get("properties", {})
            
            # 检查必需参数
            for req_param in required:
                if req_param not in parameters:
                    errors.append(f"缺少必需参数: {req_param}")
            
            # 检查参数类型
            for param_name, param_value in parameters.items():
                if param_name in properties:
                    expected_type = properties[param_name].get("type")
                    if expected_type and not self._check_type(param_value, expected_type):
                        errors.append(f"参数 {param_name} 类型错误，期望 {expected_type}")
        
        return errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查参数类型
        
        Args:
            value: 参数值
            expected_type: 期望类型
            
        Returns:
            bool: 类型是否匹配
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
    
    def register_custom_function(
        self, 
        name: str, 
        function: Callable, 
        config: Optional[TriggerFunctionConfig] = None
    ) -> None:
        """注册自定义函数
        
        Args:
            name: 函数名称
            function: 函数对象
            config: 函数配置，如果为None则创建默认配置
        """
        if config is None:
            config = TriggerFunctionConfig(
                name=name,
                description=f"自定义函数: {name}",
                function_type="custom",
                parameters={},
                implementation="custom",
                metadata={},
                dependencies=[],
                return_schema={},
                input_schema={}
            )
        
        self.registry.register_function(name, function, config)
    
    def unregister_function(self, name: str) -> bool:
        """注销函数
        
        Args:
            name: 函数名称
            
        Returns:
            bool: 是否成功注销
        """
        return self.registry.unregister_function(name)
    
    def register_composition(self, config: TriggerCompositionConfig) -> None:
        """注册触发器组合
        
        Args:
            config: 触发器组合配置
        """
        self.registry.register_composition(config)
    
    def get_composition(self, name: str) -> Optional[TriggerCompositionConfig]:
        """获取触发器组合
        
        Args:
            name: 组合名称
            
        Returns:
            Optional[TriggerCompositionConfig]: 触发器组合配置，如果不存在返回None
        """
        return self.registry.get_composition(name)
    
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
        return self.registry.get_categories()
    
    def get_functions_by_type(self, function_type: str) -> List[str]:
        """获取指定类型的函数
        
        Args:
            function_type: 函数类型
            
        Returns:
            List[str]: 函数名称列表
        """
        return self.registry.list_functions_by_type(function_type)
    
    def reload_from_config(self, config_dir: str) -> None:
        """从配置目录重新加载函数
        
        Args:
            config_dir: 配置目录路径
        """
        # 清除现有的配置函数（保留内置函数）
        rest_functions = self.registry.list_functions_by_type("evaluate") + \
                          self.registry.list_functions_by_type("execute")
        custom_functions = [name for name in self.registry.list_functions() 
                          if name not in rest_functions]
        
        for func_name in custom_functions:
            self.registry.unregister_function(func_name)
        
        # 重新加载配置
        self.loader.load_from_config_directory(config_dir)
    
    def validate_all_functions(self) -> Dict[str, List[str]]:
        """验证所有注册的函数
        
        Returns:
            Dict[str, List[str]]: 验证结果，键为函数名称，值为错误列表
        """
        results = {}
        
        for func_name in self.registry.list_functions():
            config = self.registry.get_function_config(func_name)
            if config:
                errors = []
                
                # 验证配置
                if not config.name:
                    errors.append("函数名称不能为空")
                
                if not config.description:
                    errors.append("函数描述不能为空")
                
                if not config.function_type:
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
            "total_compositions": self.registry.composition_size(),
            "function_types": {},
            "implementations": {}
        }
        
        # 按类型统计
        for func_type in self.registry.get_categories():
            functions = self.registry.list_functions_by_type(func_type)
            stats["function_types"][func_type] = len(functions)
        
        # 按实现方式统计
        for func_name in self.registry.list_functions():
            config = self.registry.get_function_config(func_name)
            if config:
                impl = config.implementation
                stats["implementations"][impl] = stats["implementations"].get(impl, 0) + 1
        
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
        composition = self.registry.get_composition(composition_name)
        if not composition:
            logger.error(f"触发器组合不存在: {composition_name}")
            return None
        
        # 获取评估函数和执行函数
        evaluate_func = self.registry.get_function(composition.evaluate_function.name)
        execute_func = self.registry.get_function(composition.execute_function.name)
        
        if not evaluate_func or not execute_func:
            logger.error(f"组合中的函数不存在: {composition_name}")
            return None
        
        # 合并配置
        trigger_config = composition.default_config.copy()
        if config:
            trigger_config.update(config)
        
        # 创建触发器
        try:
            from ..triggers.rest_triggers import CustomTrigger
            
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