"""统一工作流工厂

提供统一的工作流创建接口，整合配置驱动和简单工作流创建功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Union
from pathlib import Path
import logging

from src.infrastructure.graph.config import WorkflowConfig
from src.application.workflow.state import WorkflowState, create_message, MessageRole
from ...domain.prompts.interfaces import IPromptInjector
from ...domain.prompts.models import PromptConfig
from src.infrastructure.graph.builder import WorkflowBuilder
from src.infrastructure.graph.registry import NodeRegistry, get_global_registry
from .manager import WorkflowManager

logger = logging.getLogger(__name__)


class IWorkflowFactory(ABC):
    """工作流工厂接口"""
    
    @abstractmethod
    def create_from_config(self, config: WorkflowConfig) -> Any:
        """从配置创建工作流"""
        pass
    
    @abstractmethod
    def create_simple(self, prompt_injector: IPromptInjector, llm_client: Optional[Any] = None) -> Any:
        """创建简单工作流"""
        pass
    
    @abstractmethod
    def create_react(self, llm_client: Optional[Any] = None) -> Any:
        """创建ReAct工作流"""
        pass
    
    @abstractmethod
    def create_plan_execute(self, llm_client: Optional[Any] = None) -> Any:
        """创建Plan-Execute工作流"""
        pass


class UnifiedWorkflowFactory(IWorkflowFactory):
    """统一工作流工厂实现"""
    
    def __init__(
        self,
        node_registry: Optional[NodeRegistry] = None,
        workflow_builder: Optional[WorkflowBuilder] = None
    ) -> None:
        """初始化工作流工厂
        
        Args:
            node_registry: 节点注册表
            workflow_builder: 工作流构建器
        """
        self.node_registry = node_registry or get_global_registry()
        self.workflow_builder = workflow_builder or WorkflowBuilder(self.node_registry)
        self._predefined_configs: Dict[str, WorkflowConfig] = {}
        self._load_predefined_configs()
    
    def create_from_config(self, config: WorkflowConfig) -> Any:
        """从配置创建工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            编译后的工作流
        """
        try:
            logger.info(f"从配置创建工作流: {config.name}")
            return self.workflow_builder.build_workflow(config)
        except Exception as e:
            logger.error(f"创建工作流失败: {e}")
            raise
    
    def create_simple(self, prompt_injector: IPromptInjector, llm_client: Optional[Any] = None) -> Any:
        """创建简单工作流
        
        Args:
            prompt_injector: 提示词注入器
            llm_client: LLM客户端
            
        Returns:
            简单工作流
        """
        try:
            logger.info("创建简单工作流")
            return self._create_simple_workflow(prompt_injector, llm_client)
        except Exception as e:
            logger.error(f"创建简单工作流失败: {e}")
            raise
    
    def create_react(self, llm_client: Optional[Any] = None) -> Any:
        """创建ReAct工作流
        
        Args:
            llm_client: LLM客户端
            
        Returns:
            ReAct工作流
        """
        try:
            config = self._predefined_configs.get("react")
            if not config:
                raise ValueError("ReAct工作流配置未找到")
            
            logger.info("创建ReAct工作流")
            return self.create_from_config(config)
        except Exception as e:
            logger.error(f"创建ReAct工作流失败: {e}")
            raise
    
    def create_plan_execute(self, llm_client: Optional[Any] = None) -> Any:
        """创建Plan-Execute工作流
        
        Args:
            llm_client: LLM客户端
            
        Returns:
            Plan-Execute工作流
        """
        try:
            config = self._predefined_configs.get("plan_execute")
            if not config:
                raise ValueError("Plan-Execute工作流配置未找到")
            
            logger.info("创建Plan-Execute工作流")
            return self.create_from_config(config)
        except Exception as e:
            logger.error(f"创建Plan-Execute工作流失败: {e}")
            raise
    
    def create_collaborative(self, llm_client: Optional[Any] = None) -> Any:
        """创建协作工作流
        
        Args:
            llm_client: LLM客户端
            
        Returns:
            协作工作流
        """
        try:
            config = self._predefined_configs.get("collaborative")
            if not config:
                raise ValueError("协作工作流配置未找到")
            
            logger.info("创建协作工作流")
            return self.create_from_config(config)
        except Exception as e:
            logger.error(f"创建协作工作流失败: {e}")
            raise
    
    def create_from_file(self, config_path: str) -> Any:
        """从配置文件创建工作流
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            编译后的工作流
        """
        try:
            config = self.workflow_builder.load_workflow_config(config_path)
            return self.create_from_config(config)
        except Exception as e:
            logger.error(f"从文件创建工作流失败: {e}")
            raise
    
    def list_predefined_workflows(self) -> List[str]:
        """列出预定义的工作流
        
        Returns:
            预定义工作流名称列表
        """
        return list(self._predefined_configs.keys())
    
    def get_predefined_config(self, name: str) -> Optional[WorkflowConfig]:
        """获取预定义工作流配置
        
        Args:
            name: 工作流名称
            
        Returns:
            工作流配置，如果不存在则返回None
        """
        return self._predefined_configs.get(name)
    
    def register_predefined_config(self, name: str, config: WorkflowConfig) -> None:
        """注册预定义工作流配置
        
        Args:
            name: 工作流名称
            config: 工作流配置
        """
        self._predefined_configs[name] = config
        logger.info(f"注册预定义工作流配置: {name}")
    
    def _create_simple_workflow(self, prompt_injector: IPromptInjector, llm_client: Optional[Any] = None) -> Dict[str, Any]:
        """创建简单工作流（不依赖LangGraph）
        
        Args:
            prompt_injector: 提示词注入器
            llm_client: LLM客户端
            
        Returns:
            简单工作流字典
        """
        def run_workflow(initial_state: Optional[WorkflowState] = None) -> WorkflowState:
            """运行简单工作流"""
            if initial_state is None:
                initial_state = WorkflowState()
            
            # 注入提示词
            config = self._get_simple_prompt_config()
            state = prompt_injector.inject_prompts(initial_state, config)
            
            # 如果有LLM客户端，调用LLM
            if llm_client:
                try:
                    response = llm_client.generate(state.messages)
                    state.add_message(response)
                except Exception as e:
                    logger.error(f"LLM调用失败: {e}")
                    state.add_error({"error": str(e), "source": "llm_call"})
            
            return state
        
        return {
            "run": run_workflow,
            "description": "简单提示词注入工作流",
            "type": "simple"
        }
    
    def _get_simple_prompt_config(self) -> PromptConfig:
        """获取简单提示词配置"""
        return PromptConfig(
            system_prompt="assistant",
            rules=["safety", "format"],
            user_command="data_analysis",
            cache_enabled=True
        )
    
    def _load_predefined_configs(self) -> None:
        """加载预定义工作流配置"""
        try:
            # 尝试从配置目录加载预定义配置
            config_dir = Path("configs/workflows")
            if config_dir.exists():
                for config_file in config_dir.glob("*.yaml"):
                    try:
                        config = self.workflow_builder.load_workflow_config(str(config_file))
                        self._predefined_configs[config.name] = config
                        logger.info(f"加载预定义工作流配置: {config.name}")
                    except Exception as e:
                        logger.warning(f"加载配置文件失败 {config_file}: {e}")
        except Exception as e:
            logger.warning(f"加载预定义配置失败: {e}")
        
        # 如果没有找到配置文件，创建默认配置
        if not self._predefined_configs:
            self._create_default_configs()
    
    def _create_default_configs(self) -> None:
        """创建默认预定义配置"""
        # 创建简单的ReAct配置
        from src.application.workflow.config import NodeConfig, EdgeConfig, EdgeType

        react_config = WorkflowConfig(
            name="react",
            description="ReAct工作流模式，支持推理-行动-观察循环",
            version="1.0",
            nodes={
                "analyze": NodeConfig(
                    type="analysis_node",
                    config={
                        "llm_client": "default",
                        "system_prompt": "分析用户输入并决定是否需要调用工具"
                    }
                ),
                "execute_tool": NodeConfig(
                    type="tool_node",
                    config={
                        "tool_manager": "default"
                    }
                ),
                "final_answer": NodeConfig(
                    type="llm_node",
                    config={
                        "llm_client": "default",
                        "system_prompt": "根据上下文信息提供准确回答"
                    }
                )
            },
            edges=[
                EdgeConfig(
                    from_node="analyze",
                    to_node="execute_tool",
                    type=EdgeType.CONDITIONAL,
                    condition="has_tool_calls"
                ),
                EdgeConfig(
                    from_node="analyze",
                    to_node="final_answer",
                    type=EdgeType.CONDITIONAL,
                    condition="no_tool_calls"
                ),
                EdgeConfig(
                    from_node="execute_tool",
                    to_node="analyze",
                    type=EdgeType.SIMPLE
                )
            ],
            entry_point="analyze"
        )
        
        self._predefined_configs["react"] = react_config
        logger.info("创建默认ReAct工作流配置")


# 全局工作流工厂实例
_global_factory: Optional[UnifiedWorkflowFactory] = None


def get_global_factory() -> UnifiedWorkflowFactory:
    """获取全局工作流工厂
    
    Returns:
        全局工作流工厂实例
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = UnifiedWorkflowFactory()
    return _global_factory


def create_workflow_from_config(config: WorkflowConfig) -> Any:
    """从配置创建工作流的便捷函数
    
    Args:
        config: 工作流配置
        
    Returns:
        编译后的工作流
    """
    return get_global_factory().create_from_config(config)


def create_simple_workflow(prompt_injector: IPromptInjector, llm_client: Optional[Any] = None) -> Any:
    """创建简单工作流的便捷函数
    
    Args:
        prompt_injector: 提示词注入器
        llm_client: LLM客户端
        
    Returns:
        简单工作流
    """
    return get_global_factory().create_simple(prompt_injector, llm_client)


def create_react_workflow(llm_client: Optional[Any] = None) -> Any:
    """创建ReAct工作流的便捷函数
    
    Args:
        llm_client: LLM客户端
        
    Returns:
        ReAct工作流
    """
    return get_global_factory().create_react(llm_client)


def create_plan_execute_workflow(llm_client: Optional[Any] = None) -> Any:
    """创建Plan-Execute工作流的便捷函数
    
    Args:
        llm_client: LLM客户端
        
    Returns:
        Plan-Execute工作流
    """
    return get_global_factory().create_plan_execute(llm_client)