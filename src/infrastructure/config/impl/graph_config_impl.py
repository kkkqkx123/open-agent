"""Graph配置实现

提供Graph模块的配置加载、转换和管理功能。
专注于图的结构定义，不包含检查点等thread级概念。
"""

from typing import Dict, Any, Optional, List
import logging

from .base_impl import BaseConfigImpl
from .base_impl import IConfigSchema, ConfigProcessorChain

from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


class GraphConfigImpl(BaseConfigImpl):
    """Graph配置实现类
    
    负责Graph模块的配置加载、转换和管理。
    专注于图的结构定义，包括节点引用、边引用和状态模式。
    节点和边的具体配置由独立的配置实现处理。
    """
    
    def __init__(self, 
                 config_loader: 'IConfigLoader',
                 processor_chain: ConfigProcessorChain,
                 schema: IConfigSchema):
        """初始化Graph配置实现
        
        Args:
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
        """
        super().__init__("graph", config_loader, processor_chain, schema)
        
        # 默认图配置
        self._default_graph_config = {
            "version": "1.0",
            "enable_tracing": False,
            "retry_attempts": 3,
            "retry_delay": 1.0
        }
        
        # 支持的节点和边类型
        self._supported_node_types = ["start", "end", "condition", "tool", "llm", "custom"]
        self._supported_edge_types = ["simple", "conditional"]
        
        logger.debug("Graph配置实现初始化完成")
    
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换Graph配置
        
        将原始配置转换为标准化的Graph配置格式。
        只保留模块特定的逻辑，通用处理由处理器链完成。
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        logger.debug("开始转换Graph配置")
        
        # 1. 标准化图基本信息（模块特定）
        config = self._normalize_graph_info(config)
        
        # 2. 处理状态模式配置（模块特定）
        config = self._process_state_schema(config)
        
        # 3. 处理节点引用配置（模块特定）
        config = self._process_node_references(config)
        
        # 4. 处理边引用配置（模块特定）
        config = self._process_edge_references(config)
        
        # 注意：默认值设置、验证等通用处理已由处理器链完成
        
        logger.debug("Graph配置转换完成")
        return config
    
    def _normalize_graph_info(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化图基本信息
        
        Args:
            config: 配置数据
            
        Returns:
            标准化后的配置数据
        """
        # 确保有图名称（模块特定逻辑）
        if "name" not in config:
            config["name"] = config.get("id", "unnamed_graph")
        
        # 设置图ID（模块特定逻辑）
        if "id" not in config:
            config["id"] = config["name"]
        
        # 注意：版本默认值设置已由环境变量处理器完成
        
        return config
    
    def _process_node_references(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理节点引用配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        return self._process_nodes(config)
    
    def _process_edge_references(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理边引用配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        return self._process_edges(config)
    
    def _process_state_schema(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理状态模式配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        if "state_schema" not in config:
            config["state_schema"] = {}
        
        state_schema = config["state_schema"]
        
        # 设置默认状态名称
        state_schema.setdefault("name", "GraphState")
        
        # 处理字段配置
        if "fields" not in state_schema:
            state_schema["fields"] = {}
        
        # 添加基础字段
        base_fields = {
            "messages": {
                "type": "List[BaseMessage]",
                "reducer": "operator.add",
                "description": "对话消息历史"
            },
            "input": {
                "type": "str",
                "description": "用户输入"
            },
            "output": {
                "type": "str",
                "description": "输出结果"
            }
        }
        
        # 合并基础字段
        for field_name, field_config in base_fields.items():
            if field_name not in state_schema["fields"]:
                state_schema["fields"][field_name] = field_config
        
        # 处理字段默认值
        for field_name, field_config in state_schema["fields"].items():
            if "default" not in field_config:
                field_type = field_config.get("type", "")
                if "List" in field_type:
                    field_config["default"] = []
                elif field_type == "bool":
                    field_config["default"] = False
                elif field_type == "int":
                    field_config["default"] = 0
                elif field_type == "float":
                    field_config["default"] = 0.0
                else:
                    field_config["default"] = ""
        
        return config
    
    def _process_nodes(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理节点配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        if "nodes" not in config:
            config["nodes"] = {}
        
        nodes = config["nodes"]
        
        # 确保每个节点配置都有必要的字段
        for node_name, node_config in nodes.items():
            # 设置默认值
            node_config.setdefault("function_name", node_name)
            node_config.setdefault("description", f"节点: {node_name}")
            
            if "config" not in node_config:
                node_config["config"] = {}
            
            # 处理节点配置
            node_config["config"].setdefault("timeout", 30)
            node_config["config"].setdefault("retry_attempts", 3)
            node_config["config"].setdefault("retry_delay", 1.0)
            
            # 推断节点类型
            if "type" not in node_config:
                node_config["type"] = self._infer_node_type(node_name, node_config)
            
            # 验证节点类型
            if node_config["type"] not in self._supported_node_types:
                logger.warning(f"不支持的节点类型: {node_config['type']}")
        
        return config
    
    def _infer_node_type(self, node_name: str, node_config: Dict[str, Any]) -> str:
        """推断节点类型
        
        Args:
            node_name: 节点名称
            node_config: 节点配置
            
        Returns:
            推断的节点类型
        """
        function_name = node_config.get("function_name", node_name).lower()
        
        # 根据节点名称推断类型
        if "start" in function_name or function_name == "__start__":
            return "start"
        elif "end" in function_name or function_name == "__end__":
            return "end"
        elif "condition" in function_name or "decide" in function_name:
            return "condition"
        elif "tool" in function_name:
            return "tool"
        elif "llm" in function_name or "agent" in function_name:
            return "llm"
        else:
            return "custom"
    
    def _process_edges(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理边配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        if "edges" not in config:
            config["edges"] = []
        
        edges = config["edges"]
        
        # 确保每条边配置都有必要的字段
        for edge_config in edges:
            # 设置默认值
            edge_config.setdefault("type", "simple")
            edge_config.setdefault("description", f"边: {edge_config.get('from', '')} -> {edge_config.get('to', '')}")
            
            # 验证边类型
            if edge_config["type"] not in self._supported_edge_types:
                logger.warning(f"不支持的边类型: {edge_config['type']}")
            
            # 处理条件边
            if edge_config.get("type") == "conditional":
                if "condition" not in edge_config and "path_map" not in edge_config:
                    logger.warning("条件边缺少condition或path_map配置")
                
                # 处理路径映射
                if "path_map" in edge_config and isinstance(edge_config["path_map"], list):
                    # 转换为字典格式
                    path_map = edge_config["path_map"]
                    edge_config["path_map"] = {str(i): path for i, path in enumerate(path_map)}
        
        return config
    
    def _process_checkpointer(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理检查点配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        if "checkpointer" not in config:
            config["checkpointer"] = "memory"
        
        # 验证检查点类型
        supported_checkers = ["memory", "sqlite", "postgres", "redis"]
        if config["checkpointer"] not in supported_checkers:
            logger.warning(f"不支持的检查点类型: {config['checkpointer']}")
        
        return config
    
    def _process_interrupts(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理中断配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        # 处理中断前配置
        if "interrupt_before" not in config:
            config["interrupt_before"] = []
        elif isinstance(config["interrupt_before"], str):
            config["interrupt_before"] = [config["interrupt_before"]]
        
        # 处理中断后配置
        if "interrupt_after" not in config:
            config["interrupt_after"] = []
        elif isinstance(config["interrupt_after"], str):
            config["interrupt_after"] = [config["interrupt_after"]]
        
        return config
    
    
    
    def get_graph_config(self, graph_name: str) -> Optional[Dict[str, Any]]:
        """获取图配置
        
        Args:
            graph_name: 图名称
            
        Returns:
            图配置，如果不存在则返回None
        """
        config = self.get_config()
        
        # 检查是否为请求的图
        if config.get("name") == graph_name or config.get("id") == graph_name:
            return config.copy()
        
        return None
    
    def get_node_config(self, node_name: str) -> Optional[Dict[str, Any]]:
        """获取节点配置
        
        Args:
            node_name: 节点名称
            
        Returns:
            节点配置，如果不存在则返回None
        """
        config = self.get_config()
        nodes = config.get("nodes", {})
        
        if node_name in nodes:
            return nodes[node_name].copy()
        
        return None
    
    def get_edge_config(self, from_node: str, to_node: str) -> Optional[Dict[str, Any]]:
        """获取边配置
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
            
        Returns:
            边配置，如果不存在则返回None
        """
        config = self.get_config()
        edges = config.get("edges", [])
        
        for edge in edges:
            if (edge.get("from") == from_node and 
                edge.get("to") == to_node):
                return edge.copy()
        
        return None
    
    def get_state_schema(self) -> Dict[str, Any]:
        """获取状态模式
        
        Returns:
            状态模式配置
        """
        config = self.get_config()
        return config.get("state_schema", {}).copy()
    
    
    def list_nodes(self) -> List[str]:
        """列出所有节点
        
        Returns:
            节点名称列表
        """
        config = self.get_config()
        return list(config.get("nodes", {}).keys())
    
    def list_edges(self) -> List[Dict[str, Any]]:
        """列出所有边
        
        Returns:
            边配置列表
        """
        config = self.get_config()
        return config.get("edges", []).copy()
    
    def get_node_references(self) -> Dict[str, Dict[str, Any]]:
        """获取节点引用
        
        Returns:
            节点引用字典
        """
        config = self.get_config()
        return config.get("nodes", {}).copy()
    
    def get_edge_references(self) -> List[Dict[str, Any]]:
        """获取边引用
        
        Returns:
            边引用列表
        """
        config = self.get_config()
        return config.get("edges", []).copy()
    
    def validate_graph_config(self) -> List[str]:
        """验证图配置
        
        Returns:
            验证错误列表
        """
        errors = []
        
        try:
            config = self.get_config()
            
            # 验证基本字段
            if not config.get("name"):
                errors.append("图名称不能为空")
            
            # 验证节点
            nodes = config.get("nodes", {})
            if not nodes:
                errors.append("至少需要一个节点")
            
            # 验证边
            edges = config.get("edges", [])
            node_names = set(nodes.keys())
            
            for edge in edges:
                from_node = edge.get("from")
                to_node = edge.get("to")
                
                if from_node and from_node not in node_names and from_node != "__start__":
                    errors.append(f"边起始节点不存在: {from_node}")
                
                if to_node and to_node not in node_names and to_node != "__end__" and edge.get("type") == "simple":
                    errors.append(f"边目标节点不存在: {to_node}")
            
            # 验证入口点
            entry_point = config.get("entry_point")
            if entry_point and entry_point not in node_names:
                errors.append(f"入口点节点不存在: {entry_point}")
            
            # 验证状态模式
            state_schema = config.get("state_schema", {})
            if not state_schema.get("fields"):
                errors.append("状态模式必须包含字段定义")
            
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
            "version": config.get("version", "unknown"),
            "total_nodes": len(config.get("nodes", {})),
            "total_edges": len(config.get("edges", [])),
            "entry_point": config.get("entry_point"),
            "checkpointer": config.get("checkpointer"),
            "node_types": {},
            "edge_types": {}
        }
        
        # 统计节点类型
        for node_config in config.get("nodes", {}).values():
            node_type = node_config.get("type", "unknown")
            summary["node_types"][node_type] = summary["node_types"].get(node_type, 0) + 1
        
        # 统计边类型
        for edge in config.get("edges", []):
            edge_type = edge.get("type", "unknown")
            summary["edge_types"][edge_type] = summary["edge_types"].get(edge_type, 0) + 1
        
        return summary