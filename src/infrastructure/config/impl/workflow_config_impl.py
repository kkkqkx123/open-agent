"""Workflow配置实现

提供Workflow模块的配置加载、转换和管理功能。
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from .base_impl import BaseConfigImpl
from .base_impl import IConfigSchema, ConfigProcessorChain

from src.interfaces.config import IConfigLoader

logger = logging.getLogger(__name__)


class WorkflowConfigImpl(BaseConfigImpl):
    """Workflow配置实现类
    
    负责Workflow模块的配置加载、转换和管理。
    支持工作流配置的继承、验证和转换。
    """
    
    def __init__(self, 
                 config_loader: 'IConfigLoader',
                 processor_chain: ConfigProcessorChain,
                 schema: IConfigSchema):
        """初始化Workflow配置实现
        
        Args:
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
        """
        super().__init__("workflow", config_loader, processor_chain, schema)
        
        # 支持的工作流类型
        self._supported_workflow_types = {
            "sequential", "parallel", "conditional", "loop", "react", "state_machine"
        }
        
        # 默认工作流配置
        self._default_workflow_config = {
            "max_iterations": 10,
            "timeout": 300,
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "logging_level": "INFO",
            "enable_tracing": False
        }
        
        logger.debug("Workflow配置实现初始化完成")
    
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换Workflow配置
        
        将原始配置转换为标准化的Workflow配置格式。
        只保留模块特定的逻辑，通用处理由处理器链完成。
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        logger.debug("开始转换Workflow配置")
        
        # 1. 标准化工作流类型（模块特定）
        config = self._normalize_workflow_type(config)
        
        # 2. 处理状态模式配置（模块特定）
        config = self._process_state_schema(config)
        
        # 3. 处理节点配置（模块特定）
        config = self._process_nodes(config)
        
        # 4. 处理边配置（模块特定）
        config = self._process_edges(config)
        
        # 注意：默认值设置、验证等通用处理已由处理器链完成
        
        logger.debug("Workflow配置转换完成")
        return config
    
    def _normalize_workflow_type(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化工作流类型
        
        Args:
            config: 配置数据
            
        Returns:
            标准化后的配置数据
        """
        # 从元数据中提取工作流类型
        workflow_type = None
        if "metadata" in config:
            workflow_type = config["metadata"].get("workflow_type")
        
        # 从配置中推断工作流类型
        if not workflow_type:
            workflow_type = self._infer_workflow_type(config)
        
        # 设置工作流类型
        if workflow_type:
            config["workflow_type"] = workflow_type.lower()
            
            # 验证工作流类型是否支持
            if config["workflow_type"] not in self._supported_workflow_types:
                logger.warning(f"不支持的工作流类型: {config['workflow_type']}")
        
        return config
    
    def _infer_workflow_type(self, config: Dict[str, Any]) -> Optional[str]:
        """从配置推断工作流类型
        
        Args:
            config: 配置数据
            
        Returns:
            推断的工作流类型
        """
        # 检查是否有条件边
        edges = config.get("edges", [])
        has_conditional_edges = any(
            edge.get("type") == "conditional" for edge in edges
        )
        
        # 检查是否有循环结构
        nodes = config.get("nodes", {})
        node_names = set(nodes.keys())
        has_loop = False
        for edge in edges:
            if edge.get("from") in node_names and edge.get("to") in node_names:
                # 简单的循环检测
                if self._has_path(edge.get("to"), edge.get("from"), edges, set()):
                    has_loop = True
                    break
        
        # 检查是否有并行结构
        has_parallel = len([
            edge for edge in edges 
            if edge.get("type") == "parallel"
        ]) > 0
        
        # 根据特征推断类型
        if has_loop:
            return "loop"
        elif has_conditional_edges:
            return "conditional"
        elif has_parallel:
            return "parallel"
        elif "workflow_name" in config and "react" in config.get("workflow_name", "").lower():
            return "react"
        else:
            return "sequential"
    
    def _has_path(self, from_node: str, to_node: str, edges: List[Dict[str, Any]], visited: set) -> bool:
        """检查是否存在从from_node到to_node的路径
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
            edges: 边列表
            visited: 已访问节点
            
        Returns:
            是否存在路径
        """
        if from_node == to_node:
            return True
        
        if from_node in visited:
            return False
        
        visited.add(from_node)
        
        for edge in edges:
            if edge.get("from") == from_node:
                next_node = edge.get("to")
                if next_node and self._has_path(next_node, to_node, edges, visited.copy()):
                    return True
        
        return False
    
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
        state_schema.setdefault("name", "WorkflowState")
        
        # 处理字段配置
        if "fields" not in state_schema:
            state_schema["fields"] = {}
        
        # 添加基础字段
        base_fields = {
            "messages": {
                "type": "List[dict]",
                "default": [],
                "reducer": "extend",
                "description": "消息列表"
            },
            "input": {
                "type": "str",
                "default": "",
                "description": "输入文本"
            },
            "output": {
                "type": "str",
                "default": "",
                "description": "输出文本"
            },
            "errors": {
                "type": "List[str]",
                "default": [],
                "reducer": "extend",
                "description": "错误列表"
            }
        }
        
        # 合并基础字段
        for field_name, field_config in base_fields.items():
            if field_name not in state_schema["fields"]:
                state_schema["fields"][field_name] = field_config
        
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
            node_config.setdefault("function", node_name)
            node_config.setdefault("description", f"节点: {node_name}")
            
            if "config" not in node_config:
                node_config["config"] = {}
            
            # 处理节点配置
            node_config["config"].setdefault("timeout", 30)
            node_config["config"].setdefault("retry_attempts", 3)
            node_config["config"].setdefault("retry_delay", 1.0)
        
        return config
    
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
            
            # 处理条件边
            if edge_config.get("type") == "conditional":
                if "condition" not in edge_config and "path_map" not in edge_config:
                    logger.warning("条件边缺少condition或path_map配置")
        
        return config
    
    
    
    def get_workflow_config(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """获取工作流配置
        
        Args:
            workflow_name: 工作流名称
            
        Returns:
            工作流配置，如果不存在则返回None
        """
        config = self.get_config()
        
        # 检查是否为请求的工作流
        if config.get("workflow_name") == workflow_name:
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
    
    def validate_workflow_config(self) -> List[str]:
        """验证工作流配置
        
        Returns:
            验证错误列表
        """
        errors = []
        
        try:
            config = self.get_config()
            
            # 验证基本字段
            if not config.get("workflow_name"):
                errors.append("工作流名称不能为空")
            
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
            "workflow_name": config.get("workflow_name", "unknown"),
            "workflow_type": config.get("workflow_type", "unknown"),
            "version": config.get("metadata", {}).get("version", "unknown"),
            "total_nodes": len(config.get("nodes", {})),
            "total_edges": len(config.get("edges", [])),
            "entry_point": config.get("entry_point"),
            "max_iterations": config.get("max_iterations"),
            "timeout": config.get("timeout")
        }
        
        return summary