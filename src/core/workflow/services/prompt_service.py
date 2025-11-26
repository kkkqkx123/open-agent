"""
工作流提示词服务

提供所有工作流通用的提示词处理功能
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
import asyncio
import logging
from datetime import datetime

from src.interfaces.prompts import IPromptInjector, IPromptRegistry
from src.interfaces.prompts.models import PromptMeta
from src.core.common.exceptions.prompt import PromptNotFoundError, PromptInjectionError
from src.core.workflow.templates.workflow_template_processor import WorkflowTemplateProcessor
from src.core.state import WorkflowState

logger = logging.getLogger(__name__)


class WorkflowPromptService:
    """工作流提示词服务"""
    
    def __init__(
        self,
        prompt_registry: Optional[IPromptRegistry] = None,
        prompt_injector: Optional[IPromptInjector] = None,
        auto_initialize: bool = True,
        prompts_directory: Optional[str] = None
    ) -> None:
        self._prompt_registry = prompt_registry
        self._prompt_injector = prompt_injector
        self._template_processor = WorkflowTemplateProcessor()
        self._auto_initialize = auto_initialize
        self._prompts_directory = prompts_directory
        self._initialized = False
        self._prompt_system = None
    
    async def auto_initialize(self) -> None:
        """自动初始化提示词系统"""
        if self._initialized:
            logger.info("提示词系统已经初始化")
            return
        
        if self._auto_initialize and not self._prompt_registry:
            try:
                # 导入提示词工厂
                from src.services.prompts import create_prompt_system
                
                # 创建提示词系统
                self._prompt_system = await create_prompt_system(
                    prompts_directory=self._prompts_directory or "configs/prompts",
                    auto_discover=True
                )
                
                # 获取组件
                self._prompt_registry = self._prompt_system["registry"]
                self._prompt_injector = self._prompt_system["injector"]
                
                self._initialized = True
                logger.info("提示词系统自动初始化完成（通过配置工厂）")
                
            except Exception as e:
                logger.error(f"提示词系统自动初始化失败: {e}")
                raise
    
    def configure(
        self,
        prompt_registry: IPromptRegistry,
        prompt_injector: IPromptInjector
    ) -> None:
        """配置提示词系统"""
        self._prompt_registry = prompt_registry
        self._prompt_injector = prompt_injector
        self._initialized = True
        logger.info("工作流提示词服务已配置")
    
    async def process_prompt_content(
        self,
        content: str,
        context: Dict[str, Any],
        prompt_type: Optional[str] = None
    ) -> str:
        """处理提示词内容（通用方法）"""
        # 确保提示词系统已初始化
        if not self._initialized:
            await self.auto_initialize()
        
        try:
            # 1. 首先处理模板语法（变量替换、循环、条件等）
            processed_content = self._template_processor.process_template(content, context)
            
            # 2. 如果有提示词类型，应用类型特定的处理
            if prompt_type and self._prompt_registry:
                try:
                    from src.core.prompts.type_registry import get_global_registry
                    type_registry = get_global_registry()
                    
                    if type_registry.is_registered(prompt_type):
                        prompt_type_instance = type_registry.get_type(prompt_type)
                        processed_content = await prompt_type_instance.process_prompt(
                            processed_content, context
                        )
                except Exception as e:
                    logger.warning(f"提示词类型处理失败，使用基础处理: {e}")
            
            # 3. 处理引用解析
            if self._prompt_registry:
                processed_content = await self._resolve_references(processed_content, context)
            
            return processed_content
            
        except Exception as e:
            logger.error(f"处理提示词内容失败: {e}")
            raise PromptInjectionError(f"处理提示词内容失败: {e}")
    
    async def resolve_prompt_references(
        self,
        prompt_ids: List[str],
        context: Dict[str, Any]
    ) -> List[Any]:
        """解析提示词引用"""
        if not self._prompt_registry or not self._prompt_injector:
            raise PromptInjectionError("提示词系统未配置")
        
        try:
            # 获取提示词
            prompts = []
            for prompt_id in prompt_ids:
                try:
                    prompt = await self._prompt_registry.get(prompt_id)
                    prompts.append(prompt)
                except PromptNotFoundError:
                    logger.warning(f"提示词 '{prompt_id}' 未找到，跳过")
                    continue
            
            if not prompts:
                return []
            
            # 注入提示词
            # 由于接口签名只需要state和config，这里我们跳过直接调用
            # 创建临时的消息对象作为返回
            injected_messages = []
            for prompt in prompts:
                # 假设提示词有content属性
                if hasattr(prompt, 'content'):
                    from langchain_core.messages import SystemMessage
                    injected_messages.append(SystemMessage(content=prompt.content))
            
            return injected_messages
            
        except Exception as e:
            logger.error(f"解析提示词引用失败: {e}")
            raise PromptInjectionError(f"解析提示词引用失败: {e}")
    
    async def build_messages(
        self,
        base_messages: List[Any],
        prompt_ids: Optional[List[str]] = None,
        additional_content: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """构建完整的消息列表"""
        messages = list(base_messages)  # 复制基础消息
        
        context = context or {}
        
        # 添加提示词引用
        if prompt_ids:
            try:
                prompt_messages = await self.resolve_prompt_references(prompt_ids, context)
                messages.extend(prompt_messages)
            except Exception as e:
                logger.warning(f"添加提示词消息失败: {e}")
        
        # 添加额外内容
        if additional_content:
            try:
                processed_content = await self.process_prompt_content(additional_content, context)
                from langchain_core.messages import HumanMessage
                messages.append(HumanMessage(content=processed_content))
            except Exception as e:
                logger.warning(f"处理额外内容失败，使用原始内容: {e}")
                from langchain_core.messages import HumanMessage
                messages.append(HumanMessage(content=additional_content))
        
        return messages
    
    async def process_node_input(
        self,
        node_id: str,
        input_data: Any,
        state: WorkflowState,
        node_config: Dict[str, Any]
    ) -> Any:
        """处理节点输入（通用节点处理）"""
        try:
            # 准备上下文
            context = self._prepare_node_context(node_id, state, node_config)
            
            # 如果输入是字符串，应用提示词处理
            if isinstance(input_data, str):
                return await self.process_prompt_content(input_data, context)
            
            # 如果输入是字典，处理其中的字符串字段
            elif isinstance(input_data, dict):
                processed_input = {}
                for key, value in input_data.items():
                    if isinstance(value, str):
                        processed_input[key] = await self.process_prompt_content(value, context)
                    else:
                        processed_input[key] = value
                return processed_input
            
            # 其他类型直接返回
            return input_data
            
        except Exception as e:
            logger.warning(f"节点输入处理失败，返回原始输入: {e}")
            return input_data
    
    async def process_node_output(
        self,
        node_id: str,
        output_data: Any,
        state: WorkflowState,
        node_config: Dict[str, Any]
    ) -> Any:
        """处理节点输出（通用节点处理）"""
        try:
            # 准备上下文（包含输出数据）
            context = self._prepare_node_context(node_id, state, node_config)
            
            # 将输出数据添加到上下文中
            if isinstance(output_data, dict):
                context.update(output_data)
            else:
                context["node_output"] = output_data
            
            # 处理输出中的字符串字段
            if isinstance(output_data, dict):
                processed_output = {}
                for key, value in output_data.items():
                    if isinstance(value, str):
                        processed_output[key] = await self.process_prompt_content(value, context)
                    else:
                        processed_output[key] = value
                return processed_output
            
            return output_data
            
        except Exception as e:
            logger.warning(f"节点输出处理失败，返回原始输出: {e}")
            return output_data
    
    def _prepare_node_context(
        self,
        node_id: str,
        state: WorkflowState,
        node_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备节点上下文"""
        context = {}
        
        # 添加状态数据
        if state:
            context.update(state.get("data", {}))
        
        # 添加节点配置
        context.update({
            "node_id": node_id,
            "node_config": node_config,
            "timestamp": state.get("timestamp", "") if state else ""
        })
        
        # 添加提示词变量
        prompt_variables = node_config.get("prompt_variables", {})
        context.update(prompt_variables)
        
        return context
    
    async def _resolve_references(self, content: str, context: Dict[str, Any]) -> str:
        """解析引用"""
        try:
            if not self._prompt_registry:
                return content
            
            from src.services.prompts.reference_resolver import PromptReferenceResolver
            from src.interfaces.prompts import PromptConfig
            
            resolver = PromptReferenceResolver(
                self._prompt_registry,
                PromptConfig(
                    system_prompt="",
                    rules=[],
                    user_command="",
                    context=[],
                    examples=[],
                    constraints=[],
                    format=""
                )
            )
            
            # 创建临时提示词对象
            from src.interfaces.prompts.models import PromptType
            temp_prompt = PromptMeta.model_validate({
                "id": "temp_prompt",
                "name": "temp",
                "type": PromptType.SYSTEM,
                "content": content
            })
            
            return await resolver.resolve_references(temp_prompt, context)
            
        except Exception as e:
            logger.warning(f"引用解析失败，返回原始内容: {e}")
            return content
    
    async def validate_prompt_configuration(self, config: Dict[str, Any]) -> List[str]:
        """验证提示词配置"""
        errors = []
        
        if not self._prompt_registry or not self._prompt_injector:
            errors.append("提示词系统未配置")
            return errors
        
        # 验证提示词ID
        prompt_ids = config.get("prompt_ids", [])
        for prompt_id in prompt_ids:
            try:
                prompt = await self._prompt_registry.get(prompt_id)
                if not prompt.is_active():
                    errors.append(f"提示词 '{prompt_id}' 未激活")
            except PromptNotFoundError:
                errors.append(f"提示词 '{prompt_id}' 未找到")
        
        # 验证模板语法
        user_input = config.get("user_input")
        if user_input:
            template_errors = self._template_processor.validate_template(user_input)
            for error in template_errors:
                errors.append(f"用户输入模板错误: {error}")
        
        return errors
    
    async def preprocess_workflow_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """预处理工作流配置
        
        Args:
            config: 原始配置
            
        Returns:
            处理后的配置
        """
        processed_config = config.copy()
        
        # 处理节点配置中的提示词内容
        nodes = processed_config.get("nodes", [])
        for node in nodes:
            if "config" in node:
                # 处理节点配置中的字符串字段
                node_config = node["config"]
                for key, value in node_config.items():
                    if isinstance(value, str):
                        # 准备上下文
                        context = self._prepare_workflow_context(config, node.get("id"))
                        
                        # 处理提示词内容
                        processed_value = await self.process_prompt_content(
                            value, context
                        )
                        node_config[key] = processed_value
        
        return processed_config
    
    async def configure_workflow_nodes(self, graph: Any, config: Dict[str, Any]) -> None:
        """配置工作流节点的提示词系统
        
        Args:
            graph: 工作流图
            config: 配置
        """
        try:
            # 获取图中的所有节点
            nodes = getattr(graph, 'nodes', {})
            
            # 为每个LLM节点配置提示词系统
            for node_id, node in nodes.items():
                if hasattr(node, 'configure_prompt_system'):
                    # 获取节点特定的提示词配置
                    node_config = self._find_node_config(node_id, config)
                    if node_config:
                        # 配置节点的提示词系统
                        node.configure_prompt_system(
                            self._prompt_registry,
                            self._prompt_injector
                        )
        except Exception as e:
            logger.warning(f"配置工作流节点失败: {e}")
    
    def _prepare_workflow_context(self, config: Dict[str, Any], node_id: Optional[str] = None) -> Dict[str, Any]:
        """准备工作流上下文
        
        Args:
            config: 配置
            node_id: 节点ID
            
        Returns:
            上下文字典
        """
        context = {
            "workflow_id": config.get("workflow_id"),
            "workflow_name": config.get("name"),
            **config.get("prompt_variables", {})
        }
        
        if node_id:
            context["node_id"] = node_id
        
        return context
    
    def _find_node_config(self, node_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找特定节点的配置
        
        Args:
            node_id: 节点ID
            config: 配置
            
        Returns:
            节点配置
        """
        nodes = config.get("nodes", [])
        for node in nodes:
            if node.get("id") == node_id:
                return node.get("config", {})
        return None
    
    async def validate_workflow_structure(self, config: Dict[str, Any]) -> List[str]:
        """验证工作流结构的提示词配置
        
        Args:
            config: 配置
            
        Returns:
            验证错误列表
        """
        errors = []
        
        # 验证节点配置中的提示词引用
        nodes = config.get("nodes", [])
        for node in nodes:
            node_id = node.get("id")
            node_config = node.get("config", {})
            
            # 检查节点配置中的提示词字段
            for key, value in node_config.items():
                if isinstance(value, str) and "{{ref:" in value:
                    # 验证引用的提示词是否存在
                    try:
                        await self._validate_references_in_content(value, config)
                    except Exception as e:
                        errors.append(f"节点 {node_id} 字段 {key} 中的提示词引用无效: {e}")
        
        return errors
    
    async def _validate_references_in_content(self, content: str, config: Dict[str, Any]) -> None:
        """验证内容中的引用
        
        Args:
            content: 内容
            config: 配置
        """
        import re
        
        # 查找所有引用
        references = re.findall(r'\{\{ref:([^}]+)\}\}', content)
        
        for ref in references:
            if self._prompt_registry:
                try:
                    await self._prompt_registry.get(ref)
                except Exception:
                    raise ValueError(f"引用的提示词不存在: {ref}")
    
    async def prepare_execution_context(self, config: Optional[Dict[str, Any]], workflow_id: str, initial_state: Any) -> Dict[str, Any]:
        """准备执行上下文
        
        Args:
            config: 原始配置
            workflow_id: 工作流ID
            initial_state: 初始状态
            
        Returns:
            增强的配置
        """
        enhanced_config = config.copy() if config else {}
        
        # 准备提示词上下文
        prompt_context = {
            "workflow_id": workflow_id,
            "execution_id": enhanced_config.get("execution_id", ""),
            "timestamp": datetime.now().isoformat(),
            **(initial_state.get_data() if initial_state else {})
        }
        
        # 处理配置中的提示词变量
        prompt_variables = enhanced_config.get("prompt_variables", {})
        prompt_context.update(prompt_variables)
        
        # 处理配置中的字符串字段，应用提示词处理
        for key, value in enhanced_config.items():
            if isinstance(value, str):
                try:
                    processed_value = await self.process_prompt_content(
                        value, prompt_context
                    )
                    enhanced_config[key] = processed_value
                except Exception as e:
                    logger.warning(f"处理配置字段 '{key}' 的提示词失败: {e}")
        
        # 添加提示词服务信息到配置中
        enhanced_config["_prompt_service_info"] = self.get_service_info()
        
        return enhanced_config
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "configured": self._prompt_registry is not None and self._prompt_injector is not None,
            "template_processor_available": True,
            "prompt_system_available": self._prompt_system is not None,
            "supported_features": [
                "prompt_content_processing",
                "reference_resolution",
                "template_processing",
                "node_input_output_processing",
                "message_building",
                "workflow_config_preprocessing",
                "workflow_node_configuration",
                "workflow_structure_validation",
                "config_driven_initialization",
                "automatic_prompt_discovery"
            ]
        }
    
    async def get_prompt_system_info(self) -> Optional[Dict[str, Any]]:
        """获取提示词系统信息
        
        Returns:
            Dict[str, Any]: 提示词系统信息，如果未初始化则返回None
        """
        if self._prompt_system and self._prompt_registry:
            try:
                return {
                    "initialized": True,
                    "components": {
                        "registry": self._prompt_system["registry"] is not None,
                        "loader": self._prompt_system["loader"] is not None,
                        "injector": self._prompt_system["injector"] is not None,
                        "config_manager": self._prompt_system["config_manager"] is not None
                    }
                }
            except Exception as e:
                logger.warning(f"获取提示词系统信息失败: {e}")
                return {"initialized": True, "error": str(e)}
        return {"initialized": False}
    
    async def reload_prompts(self) -> None:
        """重新加载提示词
        
        重新创建提示词系统
        """
        try:
            from src.services.prompts import create_prompt_system
            
            # 重新创建提示词系统
            self._prompt_system = await create_prompt_system(
                prompts_directory=self._prompts_directory or "configs/prompts",
                auto_discover=True
            )
            
            # 更新组件引用
            self._prompt_registry = self._prompt_system["registry"]
            self._prompt_injector = self._prompt_system["injector"]
            
            logger.info("提示词系统重新加载完成")
            
        except Exception as e:
            logger.error(f"重新加载提示词失败: {e}")
            raise
    
    async def validate_prompt_system(self) -> List[str]:
        """验证提示词系统
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not self._prompt_system:
            errors.append("提示词系统未初始化")
            return errors
        
        if not self._prompt_registry:
            errors.append("提示词注册表未初始化")
        
        if not self._prompt_injector:
            errors.append("提示词注入器未初始化")
        
        return errors


# 全局服务实例
_global_service: Optional[WorkflowPromptService] = None


async def get_workflow_prompt_service() -> WorkflowPromptService:
    """获取全局工作流提示词服务实例"""
    global _global_service
    if _global_service is None:
        _global_service = WorkflowPromptService()
        # 确保初始化完成
        if not _global_service._initialized:
            await _global_service.auto_initialize()
    return _global_service


def get_workflow_prompt_service_sync() -> WorkflowPromptService:
    """同步获取全局工作流提示词服务实例（向后兼容）"""
    global _global_service
    if _global_service is None:
        _global_service = WorkflowPromptService(auto_initialize=False)
    return _global_service
