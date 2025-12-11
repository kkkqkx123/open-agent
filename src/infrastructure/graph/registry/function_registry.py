"""函数注册表

管理所有类型的函数注册、查询和生命周期。
这是基础设施层的核心注册表实现。
"""

from typing import Dict, Any, Optional, List
from src.interfaces.workflow.functions import (
    IFunction, INodeFunction, IConditionFunction, IRouteFunction, ITriggerFunction,
    FunctionType
)
from src.interfaces.dependency_injection import get_logger


class FunctionRegistry:
    """函数注册表
    
    管理所有类型的函数注册、查询和生命周期。
    这是基础设施层的核心注册表实现。
    """
    
    def __init__(self):
        """初始化函数注册表"""
        self.logger = get_logger(self.__class__.__name__)
        self._functions: Dict[str, IFunction] = {}
        self._type_index: Dict[FunctionType, List[str]] = {
            FunctionType.NODE: [],
            FunctionType.CONDITION: [],
            FunctionType.ROUTE: [],
            FunctionType.TRIGGER: []
        }
    
    def register(self, function: IFunction) -> None:
        """注册函数
        
        Args:
            function: 函数实例
            
        Raises:
            ValueError: 如果函数ID无效
        """
        if not function or not hasattr(function, 'function_id'):
            raise ValueError("无效的函数实例")
        
        function_id = function.function_id
        
        if not function_id:
            raise ValueError("函数ID不能为空")
        
        if function_id in self._functions:
            self.logger.warning(f"函数 '{function_id}' 已存在，将被覆盖")
        
        self._functions[function_id] = function
        
        # 更新类型索引
        func_type = function.function_type
        if function_id not in self._type_index[func_type]:
            self._type_index[func_type].append(function_id)
        
        self.logger.debug(f"注册函数: {function_id} ({func_type.value})")
    
    def unregister(self, function_id: str) -> bool:
        """注销函数
        
        Args:
            function_id: 函数ID
            
        Returns:
            bool: 是否成功注销
        """
        if function_id not in self._functions:
            return False
        
        function = self._functions[function_id]
        func_type = function.function_type
        
        # 从类型索引中移除
        if function_id in self._type_index[func_type]:
            self._type_index[func_type].remove(function_id)
        
        # 清理资源
        try:
            function.cleanup()
        except Exception as e:
            self.logger.warning(f"清理函数 '{function_id}' 时出错: {e}")
        
        del self._functions[function_id]
        self.logger.debug(f"注销函数: {function_id}")
        return True
    
    def get(self, function_id: str) -> Optional[IFunction]:
        """获取函数
        
        Args:
            function_id: 函数ID
            
        Returns:
            Optional[IFunction]: 函数实例，如果不存在返回None
        """
        return self._functions.get(function_id)
    
    def get_by_name(self, name: str) -> Optional[IFunction]:
        """按名称获取函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[IFunction]: 函数实例，如果不存在返回None
        """
        for function in self._functions.values():
            if function.name == name:
                return function
        return None
    
    def list_by_type(self, function_type: FunctionType) -> List[IFunction]:
        """按类型列出函数
        
        Args:
            function_type: 函数类型
            
        Returns:
            List[IFunction]: 函数列表
        """
        function_ids = self._type_index.get(function_type, [])
        return [self._functions[fid] for fid in function_ids if fid in self._functions]
    
    def list_all(self) -> List[IFunction]:
        """列出所有函数
        
        Returns:
            List[IFunction]: 所有函数列表
        """
        return list(self._functions.values())
    
    def get_node_functions(self) -> List[INodeFunction]:
        """获取节点函数
        
        Returns:
            List[INodeFunction]: 节点函数列表
        """
        return [f for f in self.list_by_type(FunctionType.NODE) if isinstance(f, INodeFunction)]
    
    def get_condition_functions(self) -> List[IConditionFunction]:
        """获取条件函数
        
        Returns:
            List[IConditionFunction]: 条件函数列表
        """
        return [f for f in self.list_by_type(FunctionType.CONDITION) if isinstance(f, IConditionFunction)]
    
    def get_route_functions(self) -> List[IRouteFunction]:
        """获取路由函数
        
        Returns:
            List[IRouteFunction]: 路由函数列表
        """
        return [f for f in self.list_by_type(FunctionType.ROUTE) if isinstance(f, IRouteFunction)]
    
    def get_trigger_functions(self) -> List[ITriggerFunction]:
        """获取触发器函数
        
        Returns:
            List[ITriggerFunction]: 触发器函数列表
        """
        return [f for f in self.list_by_type(FunctionType.TRIGGER) if isinstance(f, ITriggerFunction)]
    
    def clear(self, function_type: Optional[FunctionType] = None) -> None:
        """清除函数
        
        Args:
            function_type: 要清除的函数类型，None表示清除所有
        """
        if function_type:
            function_ids = self._type_index.get(function_type, []).copy()
            for function_id in function_ids:
                self.unregister(function_id)
        else:
            # 清除所有函数
            function_ids = list(self._functions.keys())
            for function_id in function_ids:
                self.unregister(function_id)
    
    def has(self, function_id: str) -> bool:
        """检查函数是否存在
        
        Args:
            function_id: 函数ID
            
        Returns:
            bool: 是否存在
        """
        return function_id in self._functions
    
    def count(self, function_type: Optional[FunctionType] = None) -> int:
        """获取函数数量
        
        Args:
            function_type: 函数类型，None表示统计所有
            
        Returns:
            int: 函数数量
        """
        if function_type:
            return len(self._type_index.get(function_type, []))
        return len(self._functions)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "total": len(self._functions),
            "by_type": {
                func_type.value: len(function_ids)
                for func_type, function_ids in self._type_index.items()
            }
        }
    
    def validate_function(self, function_id: str) -> List[str]:
        """验证函数
        
        Args:
            function_id: 函数ID
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        function = self._functions.get(function_id)
        if not function:
            errors.append(f"函数不存在: {function_id}")
            return errors
        
        # 验证基本属性
        if not function.function_id:
            errors.append("函数ID不能为空")
        
        if not function.name:
            errors.append("函数名称不能为空")
        
        if not function.description:
            errors.append("函数描述不能为空")
        
        # 验证参数定义
        try:
            parameters = function.get_parameters()
            if not isinstance(parameters, dict):
                errors.append("参数定义必须是字典类型")
        except Exception as e:
            errors.append(f"获取参数定义失败: {e}")
        
        # 验证返回类型
        try:
            return_type = function.get_return_type()
            if not return_type:
                errors.append("返回类型不能为空")
        except Exception as e:
            errors.append(f"获取返回类型失败: {e}")
        
        return errors
    
    def initialize_function(self, function_id: str, config: Dict[str, Any]) -> bool:
        """初始化函数
        
        Args:
            function_id: 函数ID
            config: 初始化配置
            
        Returns:
            bool: 初始化是否成功
        """
        function = self._functions.get(function_id)
        if not function:
            self.logger.error(f"函数不存在: {function_id}")
            return False
        
        try:
            result = function.initialize(config)
            if result:
                self.logger.debug(f"初始化函数成功: {function_id}")
            else:
                self.logger.warning(f"初始化函数失败: {function_id}")
            return result
        except Exception as e:
            self.logger.error(f"初始化函数 '{function_id}' 时出错: {e}")
            return False
    
    def initialize_all_functions(self, configs: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, bool]:
        """初始化所有函数
        
        Args:
            configs: 函数初始化配置字典
            
        Returns:
            Dict[str, bool]: 初始化结果
        """
        results = {}
        configs = configs or {}
        
        for function_id in self._functions.keys():
            config = configs.get(function_id, {})
            results[function_id] = self.initialize_function(function_id, config)
        
        return results
    
    def get_function_info(self, function_id: str) -> Optional[Dict[str, Any]]:
        """获取函数信息
        
        Args:
            function_id: 函数ID
            
        Returns:
            Optional[Dict[str, Any]]: 函数信息
        """
        function = self._functions.get(function_id)
        if not function:
            return None
        
        try:
            metadata = function.get_metadata()
            return {
                "function_id": function.function_id,
                "name": function.name,
                "description": function.description,
                "version": function.version,
                "function_type": function.function_type.value,
                "is_async": function.is_async,
                "parameters": function.get_parameters(),
                "return_type": function.get_return_type(),
                "metadata": metadata
            }
        except Exception as e:
            self.logger.error(f"获取函数 '{function_id}' 信息时出错: {e}")
            return None
    
    def search_functions(self, query: str, function_type: Optional[FunctionType] = None) -> List[IFunction]:
        """搜索函数
        
        Args:
            query: 搜索关键词
            function_type: 函数类型过滤
            
        Returns:
            List[IFunction]: 匹配的函数列表
        """
        functions = self.list_by_type(function_type) if function_type else self.list_all()
        results = []
        
        query_lower = query.lower()
        
        for function in functions:
            # 搜索名称、描述
            if (query_lower in function.name.lower() or 
                query_lower in function.description.lower()):
                results.append(function)
                continue
            
            # 搜索元数据
            try:
                metadata = function.get_metadata()
                for value in metadata.values():
                    if isinstance(value, str) and query_lower in value.lower():
                        results.append(function)
                        break
            except Exception:
                pass
        
        return results