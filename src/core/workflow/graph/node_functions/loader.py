"""节点函数加载器

从配置文件和代码中加载节点函数。
"""

import yaml
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List
import logging

from .registry import NodeFunctionRegistry, get_global_node_function_registry
from .config import NodeFunctionConfig, NodeCompositionConfig, NodeFunctionConfigLoader

logger = logging.getLogger(__name__)


class NodeFunctionLoader:
    """节点函数加载器
    
    负责从配置文件和代码中加载节点函数。
    """
    
    def __init__(self, registry: Optional[NodeFunctionRegistry] = None):
        self.registry = registry or get_global_node_function_registry()
        self._builtin_functions: Dict[str, Callable] = {}
    
    def load_from_config_directory(self, config_dir: str) -> None:
        """从配置目录加载节点函数
        
        Args:
            config_dir: 配置目录路径
        """
        config_path = Path(config_dir)
        if not config_path.exists():
            logger.warning(f"节点函数配置目录不存在: {config_dir}")
            return
        
        # 加载节点函数配置
        node_functions_dir = config_path / "node_functions"
        if node_functions_dir.exists():
            self._load_node_functions_from_directory(node_functions_dir)
        
        # 加载节点组合配置
        node_compositions_dir = config_path / "node_compositions"
        if node_compositions_dir.exists():
            self._load_node_compositions_from_directory(node_compositions_dir)
    
    def _load_node_functions_from_directory(self, dir_path: Path) -> None:
        """从目录加载节点函数配置
        
        Args:
            dir_path: 配置目录路径
        """
        for config_file in dir_path.glob("*.yaml"):
            if config_file.name.startswith("_"):
                continue  # 跳过组配置文件
                
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                self._process_node_functions_config(config_data, config_file)
                logger.debug(f"加载节点函数配置: {config_file}")
                
            except Exception as e:
                logger.error(f"加载节点函数配置失败 {config_file}: {e}")
    
    def _load_node_compositions_from_directory(self, dir_path: Path) -> None:
        """从目录加载节点组合配置
        
        Args:
            dir_path: 配置目录路径
        """
        for config_file in dir_path.glob("*.yaml"):
            if config_file.name.startswith("_"):
                continue  # 跳过组配置文件
                
            try:
                composition_config = NodeFunctionConfigLoader.load_from_file(str(config_file))
                self.registry.register_composition(composition_config)
                logger.debug(f"加载节点组合配置: {config_file}")
                
            except Exception as e:
                logger.error(f"加载节点组合配置失败 {config_file}: {e}")
    
    def _process_node_functions_config(self, config_data: Dict[str, Any], config_file: Path) -> None:
        """处理节点函数配置
        
        Args:
            config_data: 配置数据
            config_file: 配置文件路径
        """
        node_functions = config_data.get("node_functions", {})
        category = config_data.get("category", "general")
        
        for name, func_config in node_functions.items():
            # 创建节点函数配置
            node_func_config = NodeFunctionConfig(
                name=name,
                description=func_config.get("description", ""),
                function_type=func_config.get("function_type", "custom"),
                parameters=func_config.get("parameters", {}),
                implementation=func_config.get("implementation", "config"),
                metadata=func_config.get("metadata", {}),
                dependencies=func_config.get("dependencies", []),
                return_schema=func_config.get("return_schema", {}),
                input_schema=func_config.get("input_schema", {})
            )
            
            # 根据实现方式创建节点函数
            node_function = self._create_node_function(name, func_config)
            
            if node_function:
                self.registry.register_function(name, node_function, node_func_config)
    
    def _create_node_function(self, name: str, config: Dict[str, Any]) -> Optional[Callable]:
        """根据配置创建节点函数
        
        Args:
            name: 节点函数名称
            config: 节点函数配置
            
        Returns:
            Optional[Callable]: 节点函数，如果创建失败返回None
        """
        implementation = config.get("implementation", "config")
        
        if implementation == "builtin":
            return self._get_builtin_function(name)
        elif implementation == "config":
            return self._create_config_based_function(config)
        elif implementation.startswith("custom."):
            # 自定义函数，从模块加载
            module_path = implementation[7:]  # 移除 "custom." 前缀
            return self._load_custom_function(module_path)
        else:
            logger.warning(f"未知的实现方式: {implementation}")
            return None
    
    def _create_config_based_function(self, config: Dict[str, Any]) -> Callable:
        """创建基于配置的节点函数
        
        Args:
            config: 节点函数配置
            
        Returns:
            Callable: 节点函数
        """
        func_type = config.get("function_type", "custom")
        
        if func_type == "llm":
            return self._create_llm_function(config)
        elif func_type == "tool":
            return self._create_tool_function(config)
        elif func_type == "analysis":
            return self._create_analysis_function(config)
        elif func_type == "condition":
            return self._create_condition_function(config)
        elif func_type == "data_processor":
            return self._create_data_processor_function(config)
        elif func_type == "validator":
            return self._create_validator_function(config)
        elif func_type == "transformer":
            return self._create_transformer_function(config)
        else:
            logger.warning(f"未知的配置函数类型: {func_type}")
            return lambda state, **kwargs: state
    
    def _create_llm_function(self, config: Dict[str, Any]) -> Callable:
        """创建LLM函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: LLM函数
        """
        model = config.get("model", "gpt-3.5-turbo")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 1000)
        system_prompt = config.get("system_prompt", "")
        user_prompt_template = config.get("user_prompt_template", "{input}")
        
        def llm_function(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            # 这里应该实现实际的LLM调用逻辑
            # 为简化示例，我们只返回状态
            logger.debug(f"执行LLM函数: {model}")
            return state
        
        return llm_function
    
    def _create_tool_function(self, config: Dict[str, Any]) -> Callable:
        """创建工具函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 工具函数
        """
        tool_name = config.get("tool_name", "")
        tool_parameters = config.get("tool_parameters", {})
        timeout = config.get("timeout", 30)
        
        def tool_function(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            # 这里应该实现实际的工具调用逻辑
            # 为简化示例，我们只返回状态
            logger.debug(f"执行工具函数: {tool_name}")
            return state
        
        return tool_function
    
    def _create_analysis_function(self, config: Dict[str, Any]) -> Callable:
        """创建分析函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 分析函数
        """
        analysis_type = config.get("analysis_type", "content")
        keywords = config.get("keywords", [])
        case_sensitive = config.get("case_sensitive", False)
        
        def analysis_function(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            # 这里应该实现实际的分析逻辑
            # 为简化示例，我们只返回状态
            logger.debug(f"执行分析函数: {analysis_type}")
            return state
        
        return analysis_function
    
    def _create_condition_function(self, config: Dict[str, Any]) -> Callable:
        """创建条件函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 条件函数
        """
        condition_type = config.get("condition_type", "state_check")
        state_key = config.get("state_key", "")
        expected_value = config.get("expected_value", "")
        
        def condition_function(state: Dict[str, Any], **kwargs) -> str:
            # 这里应该实现实际的条件检查逻辑
            # 为简化示例，我们只返回默认值
            logger.debug(f"执行条件函数: {condition_type}")
            return "continue"
        
        return condition_function
    
    def _create_data_processor_function(self, config: Dict[str, Any]) -> Callable:
        """创建数据处理函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 数据处理函数
        """
        processor_type = config.get("processor_type", "filter")
        filter_criteria = config.get("filter_criteria", {})
        
        def data_processor_function(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            # 这里应该实现实际的数据处理逻辑
            # 为简化示例，我们只返回状态
            logger.debug(f"执行数据处理函数: {processor_type}")
            return state
        
        return data_processor_function
    
    def _create_validator_function(self, config: Dict[str, Any]) -> Callable:
        """创建验证函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 验证函数
        """
        validation_rules = config.get("validation_rules", {})
        strict_mode = config.get("strict_mode", False)
        
        def validator_function(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            # 这里应该实现实际的验证逻辑
            # 为简化示例，我们只返回状态
            logger.debug("执行验证函数")
            return state
        
        return validator_function
    
    def _create_transformer_function(self, config: Dict[str, Any]) -> Callable:
        """创建转换函数
        
        Args:
            config: 配置数据
            
        Returns:
            Callable: 转换函数
        """
        transform_rules = config.get("transform_rules", {})
        output_format = config.get("output_format", "dict")
        
        def transformer_function(state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            # 这里应该实现实际的转换逻辑
            # 为简化示例，我们只返回状态
            logger.debug("执行转换函数")
            return state
        
        return transformer_function
    
    def _get_builtin_function(self, name: str) -> Optional[Callable]:
        """获取内置函数
        
        Args:
            name: 函数名称
            
        Returns:
            Optional[Callable]: 内置函数，如果不存在返回None
        """
        return self._builtin_functions.get(name)
    
    def _load_custom_function(self, module_path: str) -> Optional[Callable]:
        """加载自定义函数
        
        Args:
            module_path: 模块路径
            
        Returns:
            Optional[Callable]: 自定义函数，如果加载失败返回None
        """
        try:
            module = importlib.import_module(module_path)
            
            # 查找节点函数
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and not name.startswith('_'):
                    return obj
            
            logger.warning(f"在模块 {module_path} 中未找到节点函数")
            return None
            
        except Exception as e:
            logger.error(f"加载自定义函数失败 {module_path}: {e}")
            return None
    
    def register_builtin_functions(self, builtin_functions: Dict[str, Callable]) -> None:
        """注册内置函数
        
        Args:
            builtin_functions: 内置函数字典
        """
        self._builtin_functions.update(builtin_functions)
        logger.debug(f"注册 {len(builtin_functions)} 个内置函数")