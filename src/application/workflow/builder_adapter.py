"""工作流构建器适配器

提供对GraphBuilder的适配，避免循环导入。
"""

from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class WorkflowBuilderAdapter:
    """工作流构建器适配器
    
    这个适配器封装了对GraphBuilder的访问，避免循环导入。
    """
    
    def __init__(self, node_registry=None, template_registry=None):
        """初始化适配器
        
        Args:
            node_registry: 节点注册表
            template_registry: 模板注册表
        """
        self._node_registry = node_registry
        self._template_registry = template_registry
        self._builder = None
    
    def _get_builder(self):
        """延迟获取GraphBuilder实例"""
        if self._builder is None:
            # 延迟导入以避免循环依赖
            from src.infrastructure.graph.builder import GraphBuilder
            from src.infrastructure.graph.registry import get_global_registry
            
            node_registry = self._node_registry or get_global_registry()
            self._builder = GraphBuilder(
                node_registry=node_registry,
                template_registry=self._template_registry
            )
        return self._builder
    
    def build_workflow(self, config):
        """构建工作流（向后兼容方法）"""
        builder = self._get_builder()
        return builder.build_graph(config)
    
    def build_graph(self, config):
        """构建图"""
        builder = self._get_builder()
        return builder.build_graph(config)
    
    def load_workflow_config(self, config_path: str):
        """加载工作流配置"""
        builder = self._get_builder()
        return builder.load_workflow_config(config_path)
    
    def validate_config(self, config):
        """验证配置"""
        builder = self._get_builder()
        return builder.validate_config(config)
    
    def build_from_yaml(self, yaml_path: str):
        """从YAML构建图"""
        builder = self._get_builder()
        return builder.build_from_yaml(yaml_path)


# 为了向后兼容，创建一个别名
WorkflowBuilder = WorkflowBuilderAdapter