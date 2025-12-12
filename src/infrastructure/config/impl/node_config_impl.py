"""Node配置实现

提供Node模块的配置加载、转换和管理功能。
专注于节点的具体配置，与Graph配置分离。
"""

from typing import Dict, Any, Optional, List
import logging

from .base_impl import BaseConfigImpl
from .base_impl import IConfigSchema, ConfigProcessorChain

from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


class NodeConfigImpl(BaseConfigImpl):
    """Node配置实现类
    
    负责Node模块的配置加载、转换和管理。
    专注于节点的具体配置，包括函数、类型、参数等。
    """
    
    def __init__(self, 
                 config_loader: 'IConfigLoader',
                 processor_chain: ConfigProcessorChain,
                 schema: IConfigSchema):
        """初始化Node配置实现
        
        Args:
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
        """
        super().__init__("node", config_loader, processor_chain, schema)
        
        # 支持的节点类型
        self._supported_node_types = {
            "llm", "tool", "condition", "start", "end", "custom", "input", "output"
        }
        
        # 默认节点配置
        self._default_node_config = {
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "enable_tracing": False,
            "log_inputs": True,
            "log_outputs": True
        }
        
        logger.debug("Node配置实现初始化完成")
    
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换Node配置
        
        将原始配置转换为标准化的Node配置格式。
        只保留模块特定的逻辑，通用处理由处理器链完成。
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        logger.debug("开始转换Node配置")
        
        # 1. 标准化节点基本信息（模块特定）
        config = self._normalize_node_info(config)
        
        # 2. 处理节点类型（模块特定）
        config = self._process_node_type(config)
        
        # 3. 处理函数配置（模块特定）
        config = self._process_function_config(config)
        
        # 4. 处理参数配置（模块特定）
        config = self._process_parameters(config)
        
        # 5. 处理输入输出配置（模块特定）
        config = self._process_io_config(config)
        
        # 注意：默认值设置、验证等通用处理已由处理器链完成
        
        logger.debug("Node配置转换完成")
        return config
    
    def _normalize_node_info(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化节点基本信息
        
        Args:
            config: 配置数据
            
        Returns:
            标准化后的配置数据
        """
        # 确保有节点名称（模块特定逻辑）
        if "name" not in config:
            config["name"] = config.get("id", "unnamed_node")
        
        # 设置节点ID（模块特定逻辑）
        if "id" not in config:
            config["id"] = config["name"]
        
        # 标准化描述（模块特定逻辑）
        config.setdefault("description", f"节点: {config['name']}")
        
        return config
    
    def _process_node_type(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理节点类型
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        # 推断节点类型
        if "type" not in config:
            config["type"] = self._infer_node_type(config)
        
        # 验证节点类型
        if config["type"] not in self._supported_node_types:
            logger.warning(f"不支持的节点类型: {config['type']}")
        
        return config
    
    def _infer_node_type(self, config: Dict[str, Any]) -> str:
        """推断节点类型
        
        Args:
            config: 配置数据
            
        Returns:
            推断的节点类型
        """
        node_name = config.get("name", "").lower()
        function_name = config.get("function_name", "").lower()
        
        # 根据节点名称推断类型
        if "start" in node_name or node_name == "__start__":
            return "start"
        elif "end" in node_name or node_name == "__end__":
            return "end"
        elif "condition" in node_name or "decide" in node_name or "judge" in node_name:
            return "condition"
        elif "input" in node_name:
            return "input"
        elif "output" in node_name:
            return "output"
        elif "tool" in function_name or "execute" in function_name:
            return "tool"
        elif "llm" in function_name or "agent" in function_name or "model" in function_name:
            return "llm"
        else:
            return "custom"
    
    def _process_function_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理函数配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        # 设置函数名称
        if "function_name" not in config:
            config["function_name"] = config["name"]
        
        # 处理函数配置
        if "function_config" not in config:
            config["function_config"] = {}
        
        function_config = config["function_config"]
        
        # 根据节点类型设置默认函数配置
        node_type = config["type"]
        if node_type == "llm":
            function_config.setdefault("model", "gpt-4")
            function_config.setdefault("temperature", 0.7)
            function_config.setdefault("max_tokens", 1000)
        elif node_type == "tool":
            function_config.setdefault("timeout", 30)
            function_config.setdefault("error_handling", "raise")
        elif node_type == "condition":
            function_config.setdefault("default_path", "false")
        
        return config
    
    def _process_parameters(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理参数配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        # 处理输入参数
        if "input_parameters" not in config:
            config["input_parameters"] = {}
        
        # 处理输出参数
        if "output_parameters" not in config:
            config["output_parameters"] = {}
        
        # 处理环境变量
        if "environment" not in config:
            config["environment"] = {}
        
        return config
    
    def _process_io_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理输入输出配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        # 处理输入映射
        if "input_mapping" not in config:
            config["input_mapping"] = {}
        
        # 处理输出映射
        if "output_mapping" not in config:
            config["output_mapping"] = {}
        
        # 处理状态更新
        if "state_updates" not in config:
            config["state_updates"] = {}
        
        return config
    
    
    
    def get_node_config(self, node_name: str) -> Optional[Dict[str, Any]]:
        """获取节点配置
        
        Args:
            node_name: 节点名称
            
        Returns:
            节点配置，如果不存在则返回None
        """
        config = self.get_config()
        
        # 检查是否为请求的节点
        if config.get("name") == node_name or config.get("id") == node_name:
            return config.copy()
        
        return None
    
    def get_function_config(self) -> Dict[str, Any]:
        """获取函数配置
        
        Returns:
            函数配置
        """
        config = self.get_config()
        return config.get("function_config", {}).copy()
    
    def get_input_parameters(self) -> Dict[str, Any]:
        """获取输入参数
        
        Returns:
            输入参数配置
        """
        config = self.get_config()
        return config.get("input_parameters", {}).copy()
    
    def get_output_parameters(self) -> Dict[str, Any]:
        """获取输出参数
        
        Returns:
            输出参数配置
        """
        config = self.get_config()
        return config.get("output_parameters", {}).copy()
    
    def get_io_mapping(self) -> Dict[str, Any]:
        """获取输入输出映射
        
        Returns:
            输入输出映射配置
        """
        config = self.get_config()
        return {
            "input_mapping": config.get("input_mapping", {}),
            "output_mapping": config.get("output_mapping", {}),
            "state_updates": config.get("state_updates", {})
        }
    
    def validate_node_config(self) -> List[str]:
        """验证节点配置
        
        Returns:
            验证错误列表
        """
        errors = []
        
        try:
            config = self.get_config()
            
            # 验证基本字段
            if not config.get("name"):
                errors.append("节点名称不能为空")
            
            if not config.get("function_name"):
                errors.append("函数名称不能为空")
            
            # 验证节点类型
            node_type = config.get("type")
            if node_type and node_type not in self._supported_node_types:
                errors.append(f"不支持的节点类型: {node_type}")
            
            # 验证特定节点类型的配置
            if node_type == "llm":
                function_config = config.get("function_config", {})
                if not function_config.get("model"):
                    errors.append("LLM节点必须指定模型")
            elif node_type == "tool":
                function_config = config.get("function_config", {})
                if not function_config.get("tool_name") and not config.get("function_name"):
                    errors.append("Tool节点必须指定工具名称或函数名称")
            
        except Exception as e:
            errors.append(f"配置验证异常: {str(e)}")
        
        return errors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            配置摘要信息
        """
        config = self.get_config()
        
        summary = {
            "name": config.get("name", "unknown"),
            "id": config.get("id", "unknown"),
            "type": config.get("type", "unknown"),
            "function_name": config.get("function_name", "unknown"),
            "timeout": config.get("timeout"),
            "retry_attempts": config.get("retry_attempts"),
            "enable_tracing": config.get("enable_tracing", False),
            "total_input_parameters": len(config.get("input_parameters", {})),
            "total_output_parameters": len(config.get("output_parameters", {}))
        }
        
        return summary