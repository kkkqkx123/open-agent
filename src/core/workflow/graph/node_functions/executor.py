"""节点函数执行器

执行节点函数和节点组合。
"""

from typing import Dict, Any, Callable, Optional, List
from src.services.logger.injection import get_logger
from datetime import datetime

from .registry import NodeFunctionRegistry
from .config import NodeCompositionConfig

logger = get_logger(__name__)


class NodeFunctionExecutor:
    """节点函数执行器
    
    负责执行节点函数和节点组合。
    """
    
    def __init__(self, registry: NodeFunctionRegistry):
        """初始化节点函数执行器
        
        Args:
            registry: 节点函数注册表
        """
        self.registry = registry
    
    def execute_function(
        self, 
        name: str, 
        state: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """执行节点函数
        
        Args:
            name: 函数名称
            state: 工作流状态
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 更新后的状态
            
        Raises:
            ValueError: 如果函数不存在
            Exception: 如果函数执行失败
        """
        function = self.registry.get_function(name)
        if not function:
            raise ValueError(f"节点函数不存在: {name}")
        
        try:
            start_time = datetime.now()
            logger.debug(f"开始执行节点函数: {name}")
            
            # 执行函数
            result = function(state, **kwargs)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            logger.debug(f"节点函数执行完成: {name} (耗时: {execution_time:.3f}s)")
            
            return result
            
        except Exception as e:
            logger.error(f"节点函数执行失败: {name} - {e}")
            raise
    
    def execute_composition(
        self, 
        name: str, 
        state: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """执行节点组合
        
        Args:
            name: 组合名称
            state: 工作流状态
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 更新后的状态
            
        Raises:
            ValueError: 如果组合不存在
            Exception: 如果执行失败
        """
        composition = self.registry.get_composition(name)
        if not composition:
            raise ValueError(f"节点组合不存在: {name}")
        
        try:
            start_time = datetime.now()
            logger.debug(f"开始执行节点组合: {name}")
            
            # 按执行顺序执行函数
            current_state = state.copy()
            
            for func_name in composition.execution_order:
                # 检查函数是否存在
                if not self.registry.has_function(func_name):
                    raise ValueError(f"组合中的函数不存在: {func_name}")
                
                # 执行函数
                current_state = self.execute_function(func_name, current_state, **kwargs)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            logger.debug(f"节点组合执行完成: {name} (耗时: {execution_time:.3f}s)")
            
            return current_state
            
        except Exception as e:
            logger.error(f"节点组合执行失败: {name} - {e}")
            raise
    
    def execute_with_error_handling(
        self, 
        name: str, 
        state: Dict[str, Any], 
        error_handler: Optional[Callable] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """执行节点函数或组合，带错误处理
        
        Args:
            name: 函数或组合名称
            state: 工作流状态
            error_handler: 错误处理函数
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 更新后的状态
        """
        try:
            # 尝试作为组合执行
            if self.registry.has_composition(name):
                return self.execute_composition(name, state, **kwargs)
            # 否则作为函数执行
            elif self.registry.has_function(name):
                return self.execute_function(name, state, **kwargs)
            else:
                raise ValueError(f"函数或组合不存在: {name}")
                
        except Exception as e:
            if error_handler:
                logger.debug(f"使用错误处理函数处理异常: {e}")
                return error_handler(state, error=e, **kwargs)
            else:
                # 添加错误信息到状态
                error_state = state.copy()
                if "errors" not in error_state:
                    error_state["errors"] = []
                error_state["errors"].append(str(e))
                return error_state