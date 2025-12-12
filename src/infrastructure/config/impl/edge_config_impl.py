"""Edge配置实现

提供Edge模块的配置加载、转换和管理功能。
专注于边的具体配置，与Graph配置分离。
"""

from typing import Dict, Any, Optional, List
import logging

from .base_impl import BaseConfigImpl, ConfigProcessorChain
from .base_impl import IConfigSchema
from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


class EdgeConfigImpl(BaseConfigImpl):
    """Edge配置实现类
    
    负责Edge模块的配置加载、转换和管理。
    专注于边的具体配置，包括类型、条件、路径映射等。
    """
    
    def __init__(self, 
                 config_loader: 'IConfigLoader',
                 processor_chain: ConfigProcessorChain,
                 schema: IConfigSchema):
        """初始化Edge配置实现
        
        Args:
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
        """
        super().__init__("edge", config_loader, processor_chain, schema)
        
        # 支持的边类型
        self._supported_edge_types = {
            "simple", "conditional", "parallel", "merge", "always", "map", "reduce"
        }
        
        # 默认边配置
        self._default_edge_config = {
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "enable_tracing": False,
            "log_execution": True
        }
        
        logger.debug("Edge配置实现初始化完成")
    
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换Edge配置
        
        将原始配置转换为标准化的Edge配置格式。
        只保留模块特定的逻辑，通用处理由处理器链完成。
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        logger.debug("开始转换Edge配置")
        
        # 1. 标准化边基本信息（模块特定）
        config = self._normalize_edge_info(config)
        
        # 2. 处理边类型（模块特定）
        config = self._process_edge_type(config)
        
        # 3. 处理节点引用（模块特定）
        config = self._process_node_references(config)
        
        # 4. 处理条件配置（模块特定）
        config = self._process_condition_config(config)
        
        # 5. 处理路径映射（模块特定）
        config = self._process_path_mapping(config)
        
        # 6. 处理数据转换（模块特定）
        config = self._process_data_transformation(config)
        
        # 注意：默认值设置、验证等通用处理已由处理器链完成
        
        logger.debug("Edge配置转换完成")
        return config
    
    def _normalize_edge_info(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化边基本信息
        
        Args:
            config: 配置数据
            
        Returns:
            标准化后的配置数据
        """
        # 确保有边名称
        if "name" not in config:
            from_node = config.get("from", "unknown")
            to_node = config.get("to", "unknown")
            config["name"] = f"{from_node}_to_{to_node}"
        
        # 设置边ID
        if "id" not in config:
            config["id"] = config["name"]
        
        # 标准化描述
        config.setdefault("description", f"边: {config.get('from', '')} -> {config.get('to', '')}")
        
        return config
    
    def _process_edge_type(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理边类型
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        # 推断边类型
        if "type" not in config:
            config["type"] = self._infer_edge_type(config)
        
        # 验证边类型
        if config["type"] not in self._supported_edge_types:
            logger.warning(f"不支持的边类型: {config['type']}")
        
        return config
    
    def _infer_edge_type(self, config: Dict[str, Any]) -> str:
        """推断边类型
        
        Args:
            config: 配置数据
            
        Returns:
            推断的边类型
        """
        # 如果有条件或路径映射，则为条件边
        if "condition" in config or "path_map" in config:
            return "conditional"
        
        # 如果有并行配置，则为并行边
        if "parallel" in config or "branch" in config:
            return "parallel"
        
        # 如果有合并配置，则为合并边
        if "merge" in config or "join" in config:
            return "merge"
        
        # 默认为简单边
        return "simple"
    
    def _process_node_references(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理节点引用
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        # 验证起始节点
        if "from" not in config:
            raise ValueError("边必须指定起始节点")
        
        # 验证目标节点（简单边必须有目标节点）
        if config.get("type") == "simple" and "to" not in config:
            raise ValueError("简单边必须指定目标节点")
        
        return config
    
    def _process_condition_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理条件配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        edge_type = config.get("type")
        
        if edge_type == "conditional":
            # 处理条件表达式
            if "condition" not in config and "path_map" not in config:
                logger.warning("条件边缺少condition或path_map配置")
            
            # 处理条件函数
            if "condition_function" not in config and "condition" in config:
                # 如果有条件表达式但没有条件函数，创建默认条件函数
                config["condition_function"] = "default_condition_evaluator"
            
            # 处理条件参数
            if "condition_parameters" not in config:
                config["condition_parameters"] = {}
        
        return config
    
    def _process_path_mapping(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理路径映射
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        edge_type = config.get("type")
        
        if edge_type == "conditional":
            # 处理路径映射
            if "path_map" in config:
                path_map = config["path_map"]
                
                # 如果是列表格式，转换为字典格式
                if isinstance(path_map, list):
                    config["path_map"] = {str(i): path for i, path in enumerate(path_map)}
                elif isinstance(path_map, dict):
                    # 确保字典格式正确
                    for key, value in path_map.items():
                        if not isinstance(value, str):
                            logger.warning(f"路径映射值应为字符串: {key} -> {value}")
                else:
                    logger.warning(f"路径映射格式不正确: {type(path_map)}")
            
            # 设置默认路径映射
            if "path_map" not in config and "condition" in config:
                config["path_map"] = {
                    "true": config.get("to", "__end__"),
                    "false": config.get("fallback", "__end__")
                }
        
        return config
    
    def _process_data_transformation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据转换
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        # 处理数据转换配置
        if "data_transformation" not in config:
            config["data_transformation"] = {}
        
        data_transformation = config["data_transformation"]
        
        # 设置默认转换配置
        data_transformation.setdefault("enabled", False)
        data_transformation.setdefault("transform_function", "identity")
        data_transformation.setdefault("transform_parameters", {})
        
        # 处理过滤配置
        if "filter" not in config:
            config["filter"] = {}
        
        filter_config = config["filter"]
        filter_config.setdefault("enabled", False)
        filter_config.setdefault("filter_function", "pass_all")
        filter_config.setdefault("filter_parameters", {})
        
        return config
    
    
    
    def get_edge_config(self, edge_name: str) -> Optional[Dict[str, Any]]:
        """获取边配置
        
        Args:
            edge_name: 边名称
            
        Returns:
            边配置，如果不存在则返回None
        """
        config = self.get_config()
        
        # 检查是否为请求的边
        if config.get("name") == edge_name or config.get("id") == edge_name:
            return config.copy()
        
        return None
    
    def get_condition_config(self) -> Dict[str, Any]:
        """获取条件配置
        
        Returns:
            条件配置
        """
        config = self.get_config()
        return {
            "condition": config.get("condition"),
            "condition_function": config.get("condition_function"),
            "condition_parameters": config.get("condition_parameters", {}),
            "path_map": config.get("path_map", {})
        }
    
    def get_transformation_config(self) -> Dict[str, Any]:
        """获取数据转换配置
        
        Returns:
            数据转换配置
        """
        config = self.get_config()
        return {
            "data_transformation": config.get("data_transformation", {}),
            "filter": config.get("filter", {})
        }
    
    def get_node_references(self) -> Dict[str, str]:
        """获取节点引用
        
        Returns:
            节点引用字典
        """
        config = self.get_config()
        return {
            "from": config.get("from", ""),
            "to": config.get("to", "")
        }
    
    def validate_edge_config(self) -> List[str]:
        """验证边配置
        
        Returns:
            验证错误列表
        """
        errors = []
        
        try:
            config = self.get_config()
            
            # 验证基本字段
            if not config.get("name"):
                errors.append("边名称不能为空")
            
            if not config.get("from"):
                errors.append("起始节点不能为空")
            
            # 验证边类型
            edge_type = config.get("type")
            if edge_type and edge_type not in self._supported_edge_types:
                errors.append(f"不支持的边类型: {edge_type}")
            
            # 验证特定边类型的配置
            if edge_type == "simple":
                if not config.get("to"):
                    errors.append("简单边必须指定目标节点")
            elif edge_type == "conditional":
                if not config.get("condition") and not config.get("path_map"):
                    errors.append("条件边必须指定condition或path_map")
                
                # 验证路径映射
                path_map = config.get("path_map", {})
                if isinstance(path_map, dict) and not path_map:
                    errors.append("条件边的路径映射不能为空")
            
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
            "from": config.get("from", "unknown"),
            "to": config.get("to", "unknown"),
            "timeout": config.get("timeout"),
            "retry_attempts": config.get("retry_attempts"),
            "enable_tracing": config.get("enable_tracing", False),
            "has_condition": "condition" in config,
            "has_path_map": "path_map" in config,
            "has_transformation": config.get("data_transformation", {}).get("enabled", False)
        }
        
        return summary