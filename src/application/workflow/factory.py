"""工作流工厂

提供统一的工作流创建接口，支持多种创建方式和配置。
"""

from typing import Dict, Any, Optional, List, Union
import logging
from pathlib import Path
from abc import ABC, abstractmethod

from src.infrastructure.graph.config import WorkflowConfig
from src.infrastructure.graph.state import WorkflowState, create_message, MessageRole, create_workflow_state
from ...domain.prompts.interfaces import IPromptInjector
from ...domain.prompts.models import PromptConfig
# GraphBuilder将通过延迟导入获取
from src.infrastructure.graph.registry import NodeRegistry, get_global_registry
from .manager import WorkflowManager

logger = logging.getLogger(__name__)


class IWorkflowFactory(ABC):
    """工作流工厂接口"""
    
    @abstractmethod
    def create_from_config(self, config: WorkflowConfig) -> Any:
        """从配置创建工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            工作流实例
        """
        pass
    
    @abstractmethod
    def create_from_template(self, template_name: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """从模板创建工作流
        
        Args:
            template_name: 模板名称
            config: 覆盖配置
            
        Returns:
            工作流实例
        """
        pass
    
    @abstractmethod
    def create_simple(self, input_text: str, **kwargs) -> Any:
        """创建简单工作流
        
        Args:
            input_text: 输入文本
            **kwargs: 其他参数
            
        Returns:
            工作流实例
        """
        pass


class UnifiedWorkflowFactory(IWorkflowFactory):
    """统一工作流工厂实现"""
    
    def __init__(
        self,
        prompt_injector: Optional[IPromptInjector] = None,
        node_registry: Optional[NodeRegistry] = None,
        workflow_builder: Optional[Any] = None
    ) -> None:
        """初始化工作流工厂
        
        Args:
            prompt_injector: 提示注入器
            node_registry: 节点注册表
            workflow_builder: 工作流构建器
        """
        self.prompt_injector = prompt_injector
        self.node_registry = node_registry or get_global_registry()
        if workflow_builder is None:
            # 延迟导入GraphBuilder以避免循环依赖
            from src.infrastructure.graph import GraphBuilder
            workflow_builder = GraphBuilder(self.node_registry)
        self.workflow_builder = workflow_builder
        self._predefined_configs: Dict[str, WorkflowConfig] = {}
        
        # 加载预定义配置
        self._load_predefined_configs()
    
    def create_from_config(self, config: WorkflowConfig) -> Any:
        """从配置创建工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            工作流实例
        """
        try:
            logger.info(f"从配置创建工作流: {config.name}")
            return self.workflow_builder.build_graph(config)
        except Exception as e:
            logger.error(f"创建工作流失败: {e}")
            raise
    
    def create_from_template(self, template_name: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """从模板创建工作流
        
        Args:
            template_name: 模板名称
            config: 覆盖配置
            
        Returns:
            工作流实例
        """
        try:
            # 尝试从模板注册表获取模板
            if hasattr(self.workflow_builder, 'template_registry') and self.workflow_builder.template_registry:
                template = self.workflow_builder.template_registry.get_template(template_name)
                if template:
                    template_config = template.create_template(config or {})
                    return self.create_from_config(template_config)
            
            # 如果没有模板注册表，尝试从预定义配置获取
            if template_name in self._predefined_configs:
                base_config = self._predefined_configs[template_name]
                if config:
                    # 合并配置
                    merged_config = self._merge_config(base_config, config)
                    return self.create_from_config(merged_config)
                else:
                    return self.create_from_config(base_config)
            
            raise ValueError(f"未找到模板: {template_name}")
        except Exception as e:
            logger.error(f"从模板创建工作流失败: {e}")
            raise
    
    def create_simple(self, input_text: str, **kwargs) -> Any:
        """创建简单工作流
        
        Args:
            input_text: 输入文本
            **kwargs: 其他参数
            
        Returns:
            工作流实例
        """
        try:
            # 创建简单的ReAct配置
            from src.infrastructure.graph.config import NodeConfig, EdgeConfig, EdgeType
            
            config = WorkflowConfig(
                name="simple_workflow",
                description="简单工作流",
                nodes={
                    "llm": NodeConfig(
                        name="llm",
                        function_name="llm_node",
                        config={}
                    )
                },
                edges=[
                    EdgeConfig(
                        from_node="llm",
                        to_node="__end__",
                        type=EdgeType.SIMPLE
                    )
                ],
                entry_point="llm"
            )
            
            return self.create_from_config(config)
        except Exception as e:
            logger.error(f"创建简单工作流失败: {e}")
            raise
    
    def create_react_workflow(self, input_text: str, **kwargs) -> Any:
        """创建ReAct工作流
        
        Args:
            input_text: 输入文本
            **kwargs: 其他参数
            
        Returns:
            工作流实例
        """
        try:
            return self.create_from_template("react", {"input": input_text, **kwargs})
        except Exception as e:
            logger.error(f"创建ReAct工作流失败: {e}")
            raise
    
    def create_plan_execute_workflow(self, input_text: str, **kwargs) -> Any:
        """创建计划执行工作流
        
        Args:
            input_text: 输入文本
            **kwargs: 其他参数
            
        Returns:
            工作流实例
        """
        try:
            return self.create_from_template("plan_execute", {"input": input_text, **kwargs})
        except Exception as e:
            logger.error(f"创建计划执行工作流失败: {e}")
            raise
    
    def load_workflow_config(self, config_path: str) -> WorkflowConfig:
        """加载工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            工作流配置
        """
        try:
            config = self.workflow_builder.load_workflow_config(config_path)
            return config
        except Exception as e:
            logger.error(f"加载工作流配置失败: {e}")
            raise
    
    def create_from_file(self, config_path: str) -> Any:
        """从文件创建工作流
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            工作流实例
        """
        try:
            config = self.load_workflow_config(config_path)
            return self.create_from_config(config)
        except Exception as e:
            logger.error(f"从文件创建工作流失败: {e}")
            raise
    
    def list_available_templates(self) -> List[str]:
        """列出可用模板
        
        Returns:
            模板名称列表
        """
        templates = list(self._predefined_configs.keys())
        
        # 如果有模板注册表，也列出其中的模板
        if hasattr(self.workflow_builder, 'template_registry') and self.workflow_builder.template_registry:
            if hasattr(self.workflow_builder.template_registry, 'list_templates'):
                templates.extend(self.workflow_builder.template_registry.list_templates())
        
        return list(set(templates))  # 去重
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板信息
        """
        if template_name in self._predefined_configs:
            config = self._predefined_configs[template_name]
            return {
                "name": config.name,
                "description": config.description,
                "version": config.version,
                "nodes": list(config.nodes.keys()),
                "edges": len(config.edges)
            }
        
        # 如果有模板注册表，尝试从中获取信息
        if hasattr(self.workflow_builder, 'template_registry') and self.workflow_builder.template_registry:
            if hasattr(self.workflow_builder.template_registry, 'get_template_info'):
                return self.workflow_builder.template_registry.get_template_info(template_name)
        
        return None
    
    def _load_predefined_configs(self) -> None:
        """加载预定义配置"""
        try:
            # 这里可以加载一些预定义的工作流配置
            # 例如从配置文件或硬编码的配置
            pass
        except Exception as e:
            logger.warning(f"加载预定义配置失败: {e}")
    
    def _merge_config(self, base_config: WorkflowConfig, override: Dict[str, Any]) -> WorkflowConfig:
        """合并配置
        
        Args:
            base_config: 基础配置
            override: 覆盖配置
            
        Returns:
            合并后的配置
        """
        # 这里实现配置合并逻辑
        # 简化实现，实际应该更复杂
        return base_config


# 全局工厂实例
_global_factory: Optional[UnifiedWorkflowFactory] = None


def get_global_factory() -> UnifiedWorkflowFactory:
    """获取全局工厂实例
    
    Returns:
        全局工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = UnifiedWorkflowFactory()
    return _global_factory


def set_global_factory(factory: UnifiedWorkflowFactory) -> None:
    """设置全局工厂实例
    
    Args:
        factory: 工厂实例
    """
    global _global_factory
    _global_factory = factory


# 便捷函数
def create_workflow_from_config(config: WorkflowConfig) -> Any:
    """从配置创建工作流
    
    Args:
        config: 工作流配置
        
    Returns:
        工作流实例
    """
    return get_global_factory().create_from_config(config)


def create_workflow_from_template(template_name: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """从模板创建工作流
    
    Args:
        template_name: 模板名称
        config: 覆盖配置
        
    Returns:
        工作流实例
    """
    return get_global_factory().create_from_template(template_name, config)


def create_simple_workflow(input_text: str, **kwargs) -> Any:
    """创建简单工作流
    
    Args:
        input_text: 输入文本
        **kwargs: 其他参数
        
    Returns:
        工作流实例
    """
    return get_global_factory().create_simple(input_text, **kwargs)


def create_react_workflow(input_text: str, **kwargs) -> Any:
    """创建ReAct工作流
    
    Args:
        input_text: 输入文本
        **kwargs: 其他参数
        
    Returns:
        工作流实例
    """
    return get_global_factory().create_react_workflow(input_text, **kwargs)


def create_plan_execute_workflow(input_text: str, **kwargs) -> Any:
    """创建计划执行工作流
    
    Args:
        input_text: 输入文本
        **kwargs: 其他参数
        
    Returns:
        工作流实例
    """
    return get_global_factory().create_plan_execute_workflow(input_text, **kwargs)