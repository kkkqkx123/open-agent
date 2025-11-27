"""LLM模块核心接口定义"""

from abc import ABC, abstractmethod
from typing import (
    Dict,
    Any,
    Optional,
    List,
    AsyncGenerator,
    Generator,
    Sequence,
    Tuple,
)
from dataclasses import dataclass

from langchain_core.messages import BaseMessage


@dataclass
class LLMResponse:
    """LLM响应数据模型"""
    
    content: str  # 响应内容
    model: Optional[str] = None  # 使用的模型名称
    finish_reason: Optional[str] = None  # 完成原因（stop/length/tool_calls等）
    tokens_used: Optional[int] = None  # 使用的token数量
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据

class ILLMClient(ABC):
    """LLM客户端接口"""

    @abstractmethod
    def __init__(self, config: Any) -> None:
        """
        初始化客户端

        Args:
            config: 客户端配置
        """
        pass

    @abstractmethod
    def generate(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        生成文本响应

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应
        """
        pass

    @abstractmethod
    async def generate_async(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        异步生成文本响应

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应
        """
        pass

    @abstractmethod
    def stream_generate_async(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成文本响应

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        pass

    @abstractmethod
    def stream_generate(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        流式生成文本响应

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        pass


    @abstractmethod
    def supports_function_calling(self) -> bool:
        """
        检查是否支持函数调用

        Returns:
            bool: 是否支持函数调用
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        pass


class ILLMCallHook(ABC):
    """LLM调用钩子接口"""

    @abstractmethod
    def before_call(
        self,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        调用前的钩子

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数
        """
        pass

    @abstractmethod
    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        调用后的钩子

        Args:
            response: 生成的响应
            messages: 原始消息列表
            parameters: 生成参数
            **kwargs: 其他参数
        """
        pass

    @abstractmethod
    def on_error(
        self,
        error: Exception,
        messages: Sequence[BaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[LLMResponse]:
        """
        错误处理钩子

        Args:
            error: 发生的错误
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            Optional[LLMResponse]: 如果可以恢复，返回替代响应；否则返回None
        """
        pass


class ILLMClientFactory(ABC):
    """LLM客户端工厂接口"""

    @abstractmethod
    def create_client(self, config: Dict[str, Any]) -> ILLMClient:
        """
        创建LLM客户端实例

        Args:
            config: 客户端配置

        Returns:
            ILLMClient: 客户端实例
        """
        pass

    @abstractmethod
    def get_cached_client(self, model_name: str) -> Optional[ILLMClient]:
        """
        获取缓存的客户端实例

        Args:
            model_name: 模型名称

        Returns:
            Optional[ILLMClient]: 缓存的客户端实例，如果不存在则返回None
        """
        pass

    @abstractmethod
    def cache_client(self, model_name: str, client: ILLMClient) -> None:
        """
        缓存客户端实例

        Args:
            model_name: 模型名称
            client: 客户端实例
        """
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """清除所有缓存的客户端实例"""
        pass


class ITaskGroupManager(ABC):
    """任务组管理器接口"""
    
    @abstractmethod
    def get_models_for_group(self, group_reference: str) -> List[str]:
        """获取组引用对应的模型列表"""
        pass
    
    @abstractmethod
    def parse_group_reference(self, reference: str) -> Tuple[str, Optional[str]]:
        """解析组引用字符串"""
        pass
    
    @abstractmethod
    def get_fallback_groups(self, group_reference: str) -> List[str]:
        """获取降级组列表"""
        pass
    
    @abstractmethod
    def get_echelon_config(self, group_name: str, echelon_name: str) -> Optional[Dict[str, Any]]:
        """获取层级配置"""
        pass
    
    @abstractmethod
    def get_group_models_by_priority(self, group_name: str) -> List[Tuple[str, int, List[str]]]:
        """按优先级获取组的模型"""
        pass
    
    @abstractmethod
    def list_task_groups(self) -> List[str]:
        """列出所有任务组名称"""
        pass


class IFallbackManager(ABC):
    """降级管理器接口"""
    
    @abstractmethod
    async def execute_with_fallback(
        self,
        primary_target: str,
        fallback_groups: List[str],
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """执行带降级的请求"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
    
    @abstractmethod
    def reset_stats(self) -> None:
        """重置统计信息"""
        pass


class IPollingPoolManager(ABC):
    """轮询池管理器接口"""
    
    @abstractmethod
    def get_pool(self, name: str) -> Optional[Any]:
        """获取轮询池"""
        pass
    
    @abstractmethod
    def list_all_status(self) -> Dict[str, Any]:
        """获取所有轮询池状态"""
        pass
    
    @abstractmethod
    async def shutdown_all(self) -> None:
        """关闭所有轮询池"""
        pass


class IClientFactory(ABC):
    """客户端工厂接口"""
    
    @abstractmethod
    def create_client(self, model_name: str) -> ILLMClient:
        """创建客户端实例"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        pass


class ILLMManager(ABC):
    """LLM管理器接口"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化LLM管理器"""
        pass
    
    @abstractmethod
    async def register_client(self, name: str, client: ILLMClient) -> None:
        """注册LLM客户端"""
        pass
    
    @abstractmethod
    async def unregister_client(self, name: str) -> None:
        """注销LLM客户端"""
        pass
    
    @abstractmethod
    async def get_client(self, name: Optional[str] = None) -> ILLMClient:
        """获取LLM客户端"""
        pass
    
    @abstractmethod
    async def list_clients(self) -> List[str]:
        """列出所有已注册的客户端"""
        pass
    
    @abstractmethod
    async def get_client_for_task(
        self,
        task_type: str,
        preferred_client: Optional[str] = None
    ) -> ILLMClient:
        """根据任务类型获取最适合的LLM客户端"""
        pass
    
    @abstractmethod
    async def execute_with_fallback(
        self,
        messages: Sequence[BaseMessage],
        task_type: Optional[str] = None,
        preferred_client: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """使用降级机制执行LLM请求"""
        pass
    
    @abstractmethod
    def stream_with_fallback(
        self,
        messages: Sequence[BaseMessage],
        task_type: Optional[str] = None,
        preferred_client: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """使用降级机制执行流式LLM请求"""
        pass
    
    @abstractmethod
    async def reload_clients(self) -> None:
        """重新加载所有LLM客户端"""
        pass


class IRetryStrategy(ABC):
    """重试策略接口"""
    
    @abstractmethod
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该重试
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            是否应该重试
        """
        pass
    
    @abstractmethod
    def get_retry_delay(self, error: Exception, attempt: int) -> float:
        """
        获取重试延迟时间
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            延迟时间（秒）
        """
        pass
    
    @abstractmethod
    def on_retry_attempt(self, error: Exception, attempt: int, delay: float) -> None:
        """
        重试尝试时的回调
        
        Args:
            error: 发生的错误
            attempt: 尝试次数
            delay: 延迟时间
        """
        pass
    
    @abstractmethod
    def on_retry_success(self, result: Any, attempt: int) -> None:
        """
        重试成功时的回调
        
        Args:
            result: 结果
            attempt: 尝试次数
        """
        pass
    
    @abstractmethod
    def on_retry_failure(self, error: Exception, total_attempts: int) -> None:
        """
        重试失败时的回调
        
        Args:
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        pass


class IRetryLogger(ABC):
    """重试日志记录器接口"""
    
    @abstractmethod
    def log_retry_attempt(self, func_name: str, error: Exception, attempt: int, delay: float) -> None:
        """
        记录重试尝试
        
        Args:
            func_name: 函数名称
            error: 发生的错误
            attempt: 尝试次数
            delay: 延迟时间
        """
        pass


class IFallbackStrategy(ABC):
    """降级策略接口"""
    
    @abstractmethod
    def should_fallback(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该降级
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            是否应该降级
        """
        pass
    
    @abstractmethod
    def get_fallback_target(self, error: Exception, attempt: int) -> Optional[str]:
        """
        获取降级目标
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            降级目标模型名称，None表示不降级
        """
        pass
    
    @abstractmethod
    def get_fallback_delay(self, error: Exception, attempt: int) -> float:
        """
        获取降级前的延迟时间
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            延迟时间（秒）
        """
        pass


class IFallbackLogger(ABC):
    """降级日志记录器接口"""
    
    @abstractmethod
    def log_fallback_attempt(self, primary_model: str, fallback_model: str,
                            error: Exception, attempt: int) -> None:
        """
        记录降级尝试
        
        Args:
            primary_model: 主模型名称
            fallback_model: 降级模型名称
            error: 发生的错误
            attempt: 尝试次数
        """
        pass
    
    @abstractmethod
    def log_fallback_success(self, primary_model: str, fallback_model: str,
                           response: LLMResponse, attempt: int) -> None:
        """
        记录降级成功
        
        Args:
            primary_model: 主模型名称
            fallback_model: 降级模型名称
            response: 响应结果
            attempt: 尝试次数
        """
        pass
    
    @abstractmethod
    def log_fallback_failure(self, primary_model: str, error: Exception,
                           total_attempts: int) -> None:
        """
        记录降级失败
        
        Args:
            primary_model: 主模型名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        pass
    
    @abstractmethod
    def log_retry_success(self, func_name: str, result: Any, attempt: int) -> None:
        """
        记录重试成功
        
        Args:
            func_name: 函数名称
            result: 结果
            attempt: 尝试次数
        """
        pass
    
    @abstractmethod
    def log_retry_failure(self, func_name: str, error: Exception, total_attempts: int) -> None:
        """
        记录重试失败
        
        Args:
            func_name: 函数名称
            error: 最后的错误
            total_attempts: 总尝试次数
        """
        pass