"""
提示词相关接口定义

提供提示词注入、加载、缓存等核心功能的接口定义
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from .state.workflow import IWorkflowState


class PromptConfig:
    """提示词配置"""
    
    def __init__(
        self,
        system_prompt: Optional[str] = None,
        rules: Optional[List[str]] = None,
        user_command: Optional[str] = None,
        context: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        format: Optional[str] = None,
        cache_enabled: bool = True,
        cache_ttl: int = 3600
    ):
        self.system_prompt = system_prompt
        self.rules = rules or []
        self.user_command = user_command
        self.context = context or []
        self.examples = examples or []
        self.constraints = constraints or []
        self.format = format
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl


class IPromptInjector(ABC):
    """提示词注入器接口"""
    
    @abstractmethod
    async def inject_prompts(
        self,
        state: "IWorkflowState",
        config: PromptConfig
    ) -> "IWorkflowState":
        """异步注入提示词到工作流状态"""
        pass
    
    @abstractmethod
    def inject_system_prompt(
        self,
        state: "IWorkflowState",
        prompt_name: str
    ) -> "IWorkflowState":
        """注入系统提示词"""
        pass
    
    @abstractmethod
    def inject_rule_prompts(
        self,
        state: "IWorkflowState",
        rule_names: List[str]
    ) -> "IWorkflowState":
        """注入规则提示词"""
        pass
    
    @abstractmethod
    def inject_user_command(
        self,
        state: "IWorkflowState",
        command_name: str
    ) -> "IWorkflowState":
        """注入用户指令"""
        pass


class IPromptLoader(ABC):
    """提示词加载器接口"""
    
    @abstractmethod
    async def load_prompt_async(self, category: str, name: str) -> str:
        """异步加载提示词"""
        pass
    
    @abstractmethod
    def load_prompt(self, category: str, name: str) -> str:
        """同步加载提示词"""
        pass
    
    @abstractmethod
    def list_prompts(self, category: Optional[str] = None) -> List[str]:
        """列出提示词"""
        pass
    
    @abstractmethod
    def exists(self, category: str, name: str) -> bool:
        """检查提示词是否存在"""
        pass


class IPromptCache(ABC):
    """提示词缓存接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """获取缓存内容"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """设置缓存内容"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除缓存内容"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        pass


class IPromptType(ABC):
    """提示词类型接口"""
    
    @property
    @abstractmethod
    def type_name(self) -> str:
        """类型名称"""
        pass
    
    @property
    @abstractmethod
    def injection_order(self) -> int:
        """注入顺序（数字越小越先注入）"""
        pass
    
    @abstractmethod
    async def process_prompt(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> str:
        """处理提示词内容"""
        pass
    
    @abstractmethod
    def create_message(self, content: str) -> Any:
        """创建消息对象"""
        pass


class IPromptRegistry(ABC):
    """提示词注册表接口"""
    
    @abstractmethod
    async def register_prompt(self, meta: "PromptMeta") -> None:
        """注册提示词"""
        pass
    
    @abstractmethod
    async def get_prompt_meta(self, category: str, name: str) -> Optional["PromptMeta"]:
        """获取提示词元信息"""
        pass
    
    @abstractmethod
    async def list_prompts(self, category: str, tags: Optional[List[str]] = None) -> List["PromptMeta"]:
        """列出提示词"""
        pass
    
    @abstractmethod
    async def resolve_dependencies(self, prompt_name: str) -> List["PromptMeta"]:
        """解析提示词依赖"""
        pass
    
    @abstractmethod
    async def validate_prompt(self, meta: "PromptMeta") -> List[str]:
        """验证提示词"""
        pass


class PromptMeta:
    """提示词元信息"""
    
    def __init__(
        self,
        name: str,
        category: str,
        path: str,
        description: str = "",
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        author: str = "system",
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        cache_ttl: int = 3600,
        validation: Optional[Dict[str, Any]] = None,
        content: str = "",
        composite: bool = False,
        components: Optional[List[Dict[str, Any]]] = None
    ):
        self.name = name
        self.category = category
        self.path = path
        self.description = description
        self.version = version
        self.tags = tags or []
        self.author = author
        self.created_at = created_at
        self.updated_at = updated_at
        self.dependencies = dependencies or []
        self.parameters = parameters or []
        self.cache_ttl = cache_ttl
        self.validation = validation or {}
        self.content = content
        self.composite = composite
        self.components = components or []


class IPromptReferenceResolver(ABC):
    """提示词引用解析器接口"""
    
    @abstractmethod
    async def resolve_references(self, config: Dict[str, Any]) -> PromptConfig:
        """解析配置中的提示词引用"""
        pass
    
    @abstractmethod
    async def resolve_reference(self, ref: str) -> str:
        """解析单个引用"""
        pass
    
    @abstractmethod
    async def resolve_references_list(self, refs: List[str]) -> List[str]:
        """解析引用列表"""
        pass