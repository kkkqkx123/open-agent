"""
提示词感知的工作流构建器

提供集成提示词系统的工作流构建功能
"""

from typing import Dict, List, Any, Optional, Union
from datetime import timedelta
import asyncio

from .....interfaces.workflow.builders import IWorkflowBuilder
from .....interfaces.workflow.core import IWorkflowGraph, INode
from .....interfaces.prompts import IPromptRegistry, IPromptInjector
from .....interfaces.prompts.models import PromptMeta, PromptConfig
from .....interfaces.state.workflow import IWorkflowState
from .....core.common.exceptions.prompts import PromptNotFoundError, PromptReferenceError
from .....core.common.exceptions.workflow import WorkflowBuilderError


class PromptAwareWorkflowBuilder(IWorkflowBuilder):
    """提示词感知的工作流构建器"""
    
    def __init__(
        self,
        prompt_registry: IPromptRegistry,
        prompt_injector: IPromptInjector,
        config: Optional[PromptConfig] = None
    ):
        self._prompt_registry = prompt_registry
        self._prompt_injector = prompt_injector
        self._config = config or PromptConfig()
        
        # 构建状态
        self._current_graph: Optional[IWorkflowGraph] = None
        self._nodes: Dict[str, INode] = {}
        self._edges: List[tuple] = []
        self._prompt_configs: Dict[str, Dict[str, Any]] = {}
    
    async def build_from_config(
        self,
        config: Dict[str, Any],
        state: Optional[IWorkflowState] = None
    ) -> IWorkflowGraph:
        """从配置构建工作流"""
        try:
            # 创建新的工作流图
            self._current_graph = await self._create_graph(config, state)
            
            # 构建节点
            await self._build_nodes(config.get("nodes", []))
            
            # 构建边
            await self._build_edges(config.get("edges", []))
            
            # 配置提示词
            await self._configure_prompts(config.get("prompts", {}))
            
            # 验证工作流
            await self._validate_workflow()
            
            return self._current_graph
            
        except Exception as e:
            raise WorkflowBuilderError(f"构建工作流失败: {e}")
    
    async def add_node(
        self,
        node_id: str,
        node_type: str,
        config: Dict[str, Any],
        prompt_config: Optional[Dict[str, Any]] = None
    ) -> INode:
        """添加节点"""
        if self._current_graph is None:
            raise WorkflowBuilderError("工作流图未初始化")
        
        try:
            # 创建节点
            node = await self._create_node(node_id, node_type, config)
            
            # 配置提示词
            if prompt_config:
                await self._configure_node_prompt(node, prompt_config)
            
            # 添加到图
            self._current_graph.add_node(node)
            self._nodes[node_id] = node
            
            return node
            
        except Exception as e:
            raise WorkflowBuilderError(f"添加节点失败: {e}")
    
    async def add_edge(
        self,
        source_node: str,
        target_node: str,
        condition: Optional[str] = None
    ) -> None:
        """添加边"""
        if self._current_graph is None:
            raise WorkflowBuilderError("工作流图未初始化")
        
        if source_node not in self._nodes:
            raise WorkflowBuilderError(f"源节点 '{source_node}' 不存在")
        
        if target_node not in self._nodes:
            raise WorkflowBuilderError(f"目标节点 '{target_node}' 不存在")
        
        try:
            # 创建边
            edge_config = {
                "source": source_node,
                "target": target_node,
                "condition": condition
            }
            
            edge = await self._create_edge(edge_config)
            self._current_graph.add_edge(edge)
            self._edges.append((source_node, target_node, condition))
            
        except Exception as e:
            raise WorkflowBuilderError(f"添加边失败: {e}")
    
    async def configure_node_prompts(
        self,
        node_id: str,
        prompt_configs: Dict[str, Any]
    ) -> None:
        """配置节点提示词"""
        if node_id not in self._nodes:
            raise WorkflowBuilderError(f"节点 '{node_id}' 不存在")
        
        node = self._nodes[node_id]
        await self._configure_node_prompt(node, prompt_configs)
    
    async def inject_prompts(
        self,
        messages: List[Any],
        prompt_ids: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """注入提示词到消息列表"""
        try:
            # 获取提示词
            prompts = []
            for prompt_id in prompt_ids:
                prompt = await self._prompt_registry.get(prompt_id)
                prompts.append(prompt)
            
            # 注入提示词
            injected_messages = await self._prompt_injector.inject_prompts(
                messages,
                prompts,
                context or {}
            )
            
            return injected_messages
            
        except Exception as e:
            raise WorkflowBuilderError(f"注入提示词失败: {e}")
    
    async def resolve_prompt_references(
        self,
        prompt_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """解析提示词引用"""
        try:
            from .reference_resolver import PromptReferenceResolver
            
            resolver = PromptReferenceResolver(
                self._prompt_registry,
                self._config
            )
            
            # 创建临时提示词对象用于解析
            temp_prompt = PromptMeta(
                id="temp",
                name="temp",
                type="system",
                content=prompt_content
            )
            
            resolved_content = await resolver.resolve_references(
                temp_prompt,
                context
            )
            
            return resolved_content
            
        except Exception as e:
            raise WorkflowBuilderError(f"解析提示词引用失败: {e}")
    
    async def get_workflow_prompts(self) -> Dict[str, PromptMeta]:
        """获取工作流中使用的所有提示词"""
        prompts = {}
        
        for node_id, prompt_config in self._prompt_configs.items():
            if "system_prompt" in prompt_config:
                prompt_id = prompt_config["system_prompt"]
                try:
                    prompt = await self._prompt_registry.get(prompt_id)
                    prompts[f"{node_id}_system"] = prompt
                except PromptNotFoundError:
                    continue
            
            if "user_prompt" in prompt_config:
                prompt_id = prompt_config["user_prompt"]
                try:
                    prompt = await self._prompt_registry.get(prompt_id)
                    prompts[f"{node_id}_user"] = prompt
                except PromptNotFoundError:
                    continue
        
        return prompts
    
    async def validate_workflow_prompts(self) -> List[str]:
        """验证工作流中的提示词"""
        errors = []
        
        for node_id, prompt_config in self._prompt_configs.items():
            # 验证系统提示词
            if "system_prompt" in prompt_config:
                prompt_id = prompt_config["system_prompt"]
                try:
                    prompt = await self._prompt_registry.get(prompt_id)
                    validation_errors = await self._validate_prompt(prompt)
                    errors.extend([
                        f"节点 {node_id} 系统提示词: {error}"
                        for error in validation_errors
                    ])
                except PromptNotFoundError:
                    errors.append(f"节点 {node_id} 系统提示词未找到: {prompt_id}")
            
            # 验证用户提示词
            if "user_prompt" in prompt_config:
                prompt_id = prompt_config["user_prompt"]
                try:
                    prompt = await self._prompt_registry.get(prompt_id)
                    validation_errors = await self._validate_prompt(prompt)
                    errors.extend([
                        f"节点 {node_id} 用户提示词: {error}"
                        for error in validation_errors
                    ])
                except PromptNotFoundError:
                    errors.append(f"节点 {node_id} 用户提示词未找到: {prompt_id}")
        
        return errors
    
    async def _create_graph(
        self,
        config: Dict[str, Any],
        state: Optional[IWorkflowState]
    ) -> IWorkflowGraph:
        """创建工作流图"""
        from .....core.workflow.graph.workflow_graph import WorkflowGraph
        
        graph_config = {
            "name": config.get("name", "unnamed_workflow"),
            "description": config.get("description", ""),
            "state": state
        }
        
        return WorkflowGraph(graph_config)
    
    async def _build_nodes(self, nodes_config: List[Dict[str, Any]]) -> None:
        """构建节点"""
        for node_config in nodes_config:
            node_id = node_config["id"]
            node_type = node_config["type"]
            config = node_config.get("config", {})
            prompt_config = node_config.get("prompts", {})
            
            await self.add_node(node_id, node_type, config, prompt_config)
    
    async def _build_edges(self, edges_config: List[Dict[str, Any]]) -> None:
        """构建边"""
        for edge_config in edges_config:
            source = edge_config["source"]
            target = edge_config["target"]
            condition = edge_config.get("condition")
            
            await self.add_edge(source, target, condition)
    
    async def _configure_prompts(self, prompts_config: Dict[str, Any]) -> None:
        """配置提示词"""
        for node_id, prompt_config in prompts_config.items():
            self._prompt_configs[node_id] = prompt_config
    
    async def _create_node(
        self,
        node_id: str,
        node_type: str,
        config: Dict[str, Any]
    ) -> INode:
        """创建节点"""
        if node_type == "llm":
            from .....core.workflow.graph.nodes.llm_node import LLMNode
            # 创建增强的LLM节点，集成提示词系统
            node = LLMNode(
                llm_client=None,  # 将在运行时设置
                prompt_registry=self._prompt_registry,
                prompt_injector=self._prompt_injector
            )
            return node
        elif node_type == "tool":
            from .....core.workflow.graph.nodes.tool_node import ToolNode
            return ToolNode(node_id, config)
        elif node_type == "condition":
            from .....core.workflow.graph.nodes.condition_node import ConditionNode
            return ConditionNode(node_id, config)
        else:
            raise WorkflowBuilderError(f"不支持的节点类型: {node_type}")
    
    async def _create_edge(self, edge_config: Dict[str, Any]) -> Any:
        """创建边"""
        from .....core.workflow.graph.edge import Edge
        return Edge(edge_config)
    
    async def _configure_node_prompt(
        self,
        node: INode,
        prompt_config: Dict[str, Any]
    ) -> None:
        """配置节点提示词"""
        # 存储提示词配置
        self._prompt_configs[node.id] = prompt_config
        
        # 如果是LLM节点，直接配置提示词
        if hasattr(node, 'configure_prompts'):
            await node.configure_prompts(prompt_config, self._prompt_registry)
    
    async def _validate_workflow(self) -> None:
        """验证工作流"""
        if not self._nodes:
            raise WorkflowBuilderError("工作流没有节点")
        
        # 检查孤立节点
        connected_nodes = set()
        for source, target, _ in self._edges:
            connected_nodes.add(source)
            connected_nodes.add(target)
        
        isolated_nodes = set(self._nodes.keys()) - connected_nodes
        if isolated_nodes and len(self._nodes) > 1:
            raise WorkflowBuilderError(f"发现孤立节点: {', '.join(isolated_nodes)}")
        
        # 验证提示词
        prompt_errors = await self.validate_workflow_prompts()
        if prompt_errors:
            raise WorkflowBuilderError(f"提示词验证失败: {'; '.join(prompt_errors)}")
    
    async def _validate_prompt(self, prompt: PromptMeta) -> List[str]:
        """验证单个提示词"""
        from .reference_resolver import PromptReferenceResolver
        
        resolver = PromptReferenceResolver(self._prompt_registry, self._config)
        return await resolver.validate_references(prompt)