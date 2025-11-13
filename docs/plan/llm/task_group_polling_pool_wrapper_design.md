# 任务组和轮询池LLM实例包装器设计

## 设计目标

创建包装器模块，使任务组和轮询池能够直接作为LLM实例供LLM节点使用，支持在`src\infrastructure\graph\nodes\llm_node.py`中直接配置和使用。

## 当前问题分析

1. **LLM节点使用限制**：当前LLM节点只能使用注入的单个LLM客户端
2. **任务组集成不足**：虽然有任务组管理器，但LLM节点无法直接使用任务组配置
3. **轮询池集成缺失**：轮询池功能无法直接在LLM节点中使用
4. **降级机制复杂**：降级逻辑分散在多个地方，不够统一

## 包装器架构设计

### 1. 核心包装器接口

```python
# src/infrastructure/llm/wrappers/base_wrapper.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..interfaces import ILLMClient
from ..models import LLMResponse

class BaseLLMWrapper(ILLMClient):
    """LLM包装器基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化包装器
        
        Args:
            name: 包装器名称
            config: 包装器配置
        """
        self.name = name
        self.config = config
        self._metadata = {}
    
    @abstractmethod
    async def generate_async(self, messages: List, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> LLMResponse:
        """异步生成"""
        pass
    
    @abstractmethod
    def generate(self, messages: List, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> LLMResponse:
        """同步生成"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取包装器元数据"""
        return self._metadata.copy()
```

### 2. 任务组包装器

```python
# src/infrastructure/llm/wrappers/task_group_wrapper.py
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_wrapper import BaseLLMWrapper
from ..task_group_manager import TaskGroupManager
from ..enhanced_fallback_manager import EnhancedFallbackManager
from ..interfaces import ILLMClient
from ..models import LLMResponse
from ..exceptions import LLMError

logger = logging.getLogger(__name__)


class TaskGroupWrapper(BaseLLMWrapper):
    """任务组LLM包装器"""
    
    def __init__(self, 
                 name: str,
                 task_group_manager: TaskGroupManager,
                 fallback_manager: Optional[EnhancedFallbackManager] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化任务组包装器
        
        Args:
            name: 包装器名称
            task_group_manager: 任务组管理器
            fallback_manager: 降级管理器
            config: 包装器配置
        """
        super().__init__(name, config or {})
        self.task_group_manager = task_group_manager
        self.fallback_manager = fallback_manager
        self._current_target = None
        self._attempt_count = 0
        self._fallback_history = []
    
    async def generate_async(self, messages: List, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> LLMResponse:
        """异步生成"""
        try:
            # 获取目标配置
            target = self._get_target()
            
            # 使用降级管理器执行
            if self.fallback_manager:
                return await self._generate_with_fallback(messages, parameters, **kwargs)
            else:
                return await self._generate_direct(messages, parameters, **kwargs)
                
        except Exception as e:
            logger.error(f"任务组包装器生成失败: {e}")
            raise LLMError(f"任务组包装器生成失败: {e}")
    
    def generate(self, messages: List, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> LLMResponse:
        """同步生成"""
        try:
            # 运行异步方法
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环已经在运行，创建新的任务
                return asyncio.create_task(
                    self.generate_async(messages, parameters, **kwargs)
                ).result()
            else:
                return loop.run_until_complete(
                    self.generate_async(messages, parameters, **kwargs)
                )
        except Exception as e:
            logger.error(f"任务组包装器同步生成失败: {e}")
            raise LLMError(f"任务组包装器同步生成失败: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "type": "task_group_wrapper",
            "name": self.name,
            "current_target": self._current_target,
            "fallback_history": self._fallback_history,
            "task_group_manager": self.task_group_manager is not None,
            "fallback_manager": self.fallback_manager is not None
        }
    
    def _get_target(self) -> str:
        """获取当前目标"""
        # 从配置获取目标，如果没有则使用包装器名称
        target = self.config.get("target", self.name)
        self._current_target = target
        return target
    
    async def _generate_with_fallback(self, messages: List, parameters: Optional[Dict[str, Any]], **kwargs) -> LLMResponse:
        """使用降级机制生成"""
        target = self._get_target()
        
        # 获取降级配置
        fallback_groups = self._get_fallback_groups(target)
        
        try:
            # 使用降级管理器执行
            result = await self.fallback_manager.execute_with_fallback(
                primary_target=target,
                fallback_groups=fallback_groups,
                prompt=self._messages_to_prompt(messages),
                parameters=parameters,
                **kwargs
            )
            
            # 记录成功
            self._record_success(target)
            return self._create_llm_response(result)
            
        except Exception as e:
            # 记录失败
            self._record_failure(target, str(e))
            raise e
    
    async def _generate_direct(self, messages: List, parameters: Optional[Dict[str, Any]], **kwargs) -> LLMResponse:
        """直接生成（无降级）"""
        target = self._get_target()
        
        try:
            # 获取模型列表
            models = self.task_group_manager.get_models_for_group(target)
            if not models:
                raise LLMError(f"没有找到模型: {target}")
            
            # 选择第一个模型
            model_name = models[0]
            
            # TODO: 这里需要创建实际的LLM客户端
            # 暂时返回模拟响应
            content = f"模拟响应 from {model_name}: {self._messages_to_prompt(messages)}"
            
            return LLMResponse(
                content=content,
                model_name=model_name,
                token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                metadata={"target": target, "model": model_name}
            )
            
        except Exception as e:
            logger.error(f"直接生成失败: {e}")
            raise e
    
    def _get_fallback_groups(self, target: str) -> List[str]:
        """获取降级组列表"""
        # 从任务组配置获取降级组
        group_name, _ = self.task_group_manager.parse_group_reference(target)
        if group_name:
            return self.task_group_manager.get_fallback_groups(target)
        
        # 从包装器配置获取降级组
        return self.config.get("fallback_groups", [])
    
    def _messages_to_prompt(self, messages: List) -> str:
        """将消息列表转换为提示词"""
        if not messages:
            return ""
        
        # 简单的消息转换
        prompt_parts = []
        for message in messages:
            if hasattr(message, 'content'):
                prompt_parts.append(str(message.content))
            else:
                prompt_parts.append(str(message))
        
        return "\n".join(prompt_parts)
    
    def _create_llm_response(self, result: Any) -> LLMResponse:
        """创建LLM响应"""
        # 这里需要根据实际结果格式进行转换
        return LLMResponse(
            content=str(result),
            model_name=self._current_target or "unknown",
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            metadata={"wrapper": "task_group", "target": self._current_target}
        )
    
    def _record_success(self, target: str) -> None:
        """记录成功"""
        self._fallback_history.append({
            "target": target,
            "success": True,
            "timestamp": datetime.now().isoformat()
        })
    
    def _record_failure(self, target: str, error: str) -> None:
        """记录失败"""
        self._fallback_history.append({
            "target": target,
            "success": False,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
```

### 3. 轮询池包装器

```python
# src/infrastructure/llm/wrappers/polling_pool_wrapper.py
import asyncio
import logging
from typing import Dict, Any, Optional, List

from .base_wrapper import BaseLLMWrapper
from ..polling_pool import PollingPoolManager, LLMPollingPool
from ..interfaces import ILLMClient
from ..models import LLMResponse
from ..exceptions import LLMError

logger = logging.getLogger(__name__)


class PollingPoolWrapper(BaseLLMWrapper):
    """轮询池LLM包装器"""
    
    def __init__(self,
                 name: str,
                 polling_pool_manager: PollingPoolManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化轮询池包装器
        
        Args:
            name: 包装器名称
            polling_pool_manager: 轮询池管理器
            config: 包装器配置
        """
        super().__init__(name, config or {})
        self.polling_pool_manager = polling_pool_manager
        self._pool = None
        self._attempt_count = 0
        self._rotation_history = []
    
    async def generate_async(self, messages: List, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> LLMResponse:
        """异步生成"""
        try:
            # 获取轮询池
            pool = self._get_pool()
            if not pool:
                raise LLMError(f"轮询池不可用: {self.name}")
            
            # 使用轮询池调用
            prompt = self._messages_to_prompt(messages)
            
            # 使用简单降级策略
            result = await self._call_with_simple_fallback(pool, prompt, parameters, **kwargs)
            
            return self._create_llm_response(result, pool.name)
            
        except Exception as e:
            logger.error(f"轮询池包装器生成失败: {e}")
            raise LLMError(f"轮询池包装器生成失败: {e}")
    
    def generate(self, messages: List, parameters: Optional[Dict[str, Any]] = None, **kwargs) -> LLMResponse:
        """同步生成"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.create_task(
                    self.generate_async(messages, parameters, **kwargs)
                ).result()
            else:
                return loop.run_until_complete(
                    self.generate_async(messages, parameters, **kwargs)
                )
        except Exception as e:
            logger.error(f"轮询池包装器同步生成失败: {e}")
            raise LLMError(f"轮询池包装器同步生成失败: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pool = self._get_pool()
        pool_info = {}
        if pool:
            pool_info = {
                "name": pool.name,
                "task_groups": pool.config.task_groups,
                "rotation_strategy": pool.config.rotation_strategy,
                "instance_count": len(pool.instances),
                "healthy_instances": len([i for i in pool.instances if i.status.value == "healthy"])
            }
        
        return {
            "type": "polling_pool_wrapper",
            "name": self.name,
            "pool_info": pool_info,
            "attempt_count": self._attempt_count,
            "rotation_history": self._rotation_history
        }
    
    def _get_pool(self) -> Optional[LLMPollingPool]:
        """获取轮询池实例"""
        if self._pool is None:
            self._pool = self.polling_pool_manager.get_pool(self.name)
        return self._pool
    
    async def _call_with_simple_fallback(self, pool: LLMPollingPool, prompt: str, parameters: Optional[Dict[str, Any]], **kwargs) -> Any:
        """使用简单降级策略调用"""
        max_attempts = self.config.get("max_instance_attempts", 2)
        
        for attempt in range(max_attempts):
            try:
                # 从轮询池获取实例
                instance = pool.scheduler.select_instance(pool.instances)
                if not instance:
                    continue
                
                # 记录旋转历史
                self._rotation_history.append({
                    "instance_id": instance.instance_id,
                    "attempt": attempt + 1,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 调用实例
                # TODO: 这里需要实际的LLM客户端调用
                result = f"轮询池响应 from {instance.instance_id}: {prompt[:50]}..."
                
                # 更新统计
                instance.success_count += 1
                self._attempt_count += 1
                
                return result
                
            except Exception as e:
                logger.warning(f"实例调用失败: {instance.instance_id}, 错误: {e}")
                instance.failure_count += 1
                self._attempt_count += 1
                continue
        
        raise LLMError(f"轮询池所有实例尝试失败，尝试次数: {max_attempts}")
    
    def _messages_to_prompt(self, messages: List) -> str:
        """将消息列表转换为提示词"""
        if not messages:
            return ""
        
        prompt_parts = []
        for message in messages:
            if hasattr(message, 'content'):
                prompt_parts.append(str(message.content))
            else:
                prompt_parts.append(str(message))
        
        return "\n".join(prompt_parts)
    
    def _create_llm_response(self, result: Any, pool_name: str) -> LLMResponse:
        """创建LLM响应"""
        return LLMResponse(
            content=str(result),
            model_name=f"{pool_name}_pool",
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            metadata={
                "wrapper": "polling_pool",
                "pool_name": pool_name,
                "attempt_count": self._attempt_count
            }
        )
```

### 4. 包装器工厂

```python
# src/infrastructure/llm/wrappers/wrapper_factory.py
import logging
from typing import Dict, Any, Optional

from .task_group_wrapper import TaskGroupWrapper
from .polling_pool_wrapper import PollingPoolWrapper
from ..task_group_manager import TaskGroupManager
from ..polling_pool import PollingPoolManager
from ..enhanced_fallback_manager import EnhancedFallbackManager

logger = logging.getLogger(__name__)


class LLMWrapperFactory:
    """LLM包装器工厂"""
    
    def __init__(self,
                 task_group_manager: TaskGroupManager,
                 polling_pool_manager: Optional[PollingPoolManager] = None,
                 fallback_manager: Optional[EnhancedFallbackManager] = None):
        """
        初始化包装器工厂
        
        Args:
            task_group_manager: 任务组管理器
            polling_pool_manager: 轮询池管理器
            fallback_manager: 降级管理器
        """
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        self.fallback_manager = fallback_manager
        self._wrappers: Dict[str, Any] = {}
    
    def create_task_group_wrapper(self, name: str, config: Optional[Dict[str, Any]] = None) -> TaskGroupWrapper:
        """创建任务组包装器"""
        wrapper = TaskGroupWrapper(
            name=name,
            task_group_manager=self.task_group_manager,
            fallback_manager=self.fallback_manager,
            config=config
        )
        
        self._wrappers[name] = wrapper
        logger.info(f"创建任务组包装器: {name}")
        return wrapper
    
    def create_polling_pool_wrapper(self, name: str, config: Optional[Dict[str, Any]] = None) -> PollingPoolWrapper:
        """创建轮询池包装器"""
        if not self.polling_pool_manager:
            raise ValueError("轮询池管理器未配置")
        
        wrapper = PollingPoolWrapper(
            name=name,
            polling_pool_manager=self.polling_pool_manager,
            config=config
        )
        
        self._wrappers[name] = wrapper
        logger.info(f"创建轮询池包装器: {name}")
        return wrapper
    
    def get_wrapper(self, name: str) -> Optional[Any]:
        """获取包装器"""
        return self._wrappers.get(name)
    
    def list_wrappers(self) -> Dict[str, str]:
        """列出所有包装器"""
        return {name: type(wrapper).__name__ for name, wrapper in self._wrappers.items()}
    
    def remove_wrapper(self, name: str) -> bool:
        """移除包装器"""
        if name in self._wrappers:
            del self._wrappers[name]
            logger.info(f"移除包装器: {name}")
            return True
        return False
```

## LLM节点集成方案

### 1. 修改LLM节点构造函数

```python
# src/infrastructure/graph/nodes/llm_node.py
from src.infrastructure.llm.wrappers.wrapper_factory import LLMWrapperFactory

@node("llm_node")
class LLMNode(BaseNode):
    def __init__(self, 
                 llm_client: ILLMClient, 
                 task_group_manager: Optional[TaskGroupManager] = None,
                 wrapper_factory: Optional[LLMWrapperFactory] = None) -> None:
        """
        初始化LLM节点
        
        Args:
            llm_client: LLM客户端实例（必需）
            task_group_manager: 任务组管理器（可选）
            wrapper_factory: 包装器工厂（可选）
        """
        self._llm_client = llm_client
        self._task_group_manager = task_group_manager
        self._wrapper_factory = wrapper_factory
```

### 2. 增强执行逻辑

```python
def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
    """执行LLM调用逻辑"""
    # 合并默认配置和运行时配置
    config_loader = get_node_config_loader()
    merged_config = config_loader.merge_configs(self.node_type, config)
    
    # 选择LLM客户端
    llm_client = self._select_llm_client(merged_config)
    
    # 构建系统提示词
    system_prompt = self._build_system_prompt(state, merged_config)
    
    # 准备消息
    messages = self._prepare_messages(state, system_prompt)
    
    # 设置生成参数
    parameters = self._prepare_parameters(merged_config)
    
    # 调用LLM
    response = llm_client.generate(messages=messages, parameters=parameters)
    
    # ... 其余逻辑保持不变
```

### 3. 添加客户端选择逻辑

```python
def _select_llm_client(self, config: Dict[str, Any]) -> ILLMClient:
    """选择LLM客户端
    
    Args:
        config: 节点配置
        
    Returns:
        ILLMClient: 选定的LLM客户端
    """
    # 优先级1: 使用包装器
    if self._wrapper_factory:
        wrapper_name = config.get("llm_wrapper")
        if wrapper_name:
            wrapper = self._wrapper_factory.get_wrapper(wrapper_name)
            if wrapper:
                return wrapper
    
    # 优先级2: 使用任务组
    if self._task_group_manager and "llm_group" in config:
        return self._get_llm_client_from_group(config)
    
    # 优先级3: 使用轮询池
    if self._task_group_manager and "polling_pool" in config:
        return self._get_llm_client_from_pool(config)
    
    # 默认: 使用注入的客户端
    return self._llm_client
```

### 4. 更新配置Schema

```python
def get_config_schema(self) -> Dict[str, Any]:
    """获取节点配置Schema"""
    return {
        "type": "object",
        "properties": {
            "llm_wrapper": {
                "type": "string",
                "description": "LLM包装器名称（如 'fast_group_wrapper' 或 'thinking_pool_wrapper'）"
            },
            "llm_group": {
                "type": "string",
                "description": "LLM任务组引用，如 'fast_group.echelon1'"
            },
            "polling_pool": {
                "type": "string", 
                "description": "轮询池名称，如 'fast_pool'"
            },
            "llm_client": {
                "type": "string",
                "description": "LLM客户端配置名称（传统方式）"
            },
            # ... 其他现有配置
        }
    }
```

## 使用示例

### 1. 任务组包装器使用

```python
# 创建工作流时配置LLM节点
workflow_config = {
    "nodes": {
        "llm_node": {
            "type": "llm_node",
            "config": {
                "llm_wrapper": "fast_group_wrapper",
                "system_prompt": "你是一个快速响应的助手",
                "max_tokens": 1000
            }
        }
    }
}
```

### 2. 轮询池包装器使用

```python
# 使用轮询池包装器
workflow_config = {
    "nodes": {
        "llm_node": {
            "type": "llm_node", 
            "config": {
                "llm_wrapper": "thinking_pool_wrapper",
                "system_prompt": "你是一个深度思考的助手",
                "max_tokens": 4000
            }
        }
    }
}
```

### 3. 传统方式（向后兼容）

```python
# 继续使用传统LLM客户端
workflow_config = {
    "nodes": {
        "llm_node": {
            "type": "llm_node",
            "config": {
                "llm_client": "openai-gpt4",
                "system_prompt": "你是一个智能助手"
            }
        }
    }
}
```

## 初始化流程

```python
# 在工作流引擎初始化时
from src.infrastructure.llm.wrappers.wrapper_factory import LLMWrapperFactory

# 创建包装器工厂
wrapper_factory = LLMWrapperFactory(
    task_group_manager=task_group_manager,
    polling_pool_manager=polling_pool_manager,
    fallback_manager=fallback_manager
)

# 创建包装器
fast_wrapper = wrapper_factory.create_task_group_wrapper("fast_group_wrapper", {
    "target": "fast_group.echelon1",
    "fallback_groups": ["fast_group.echelon2", "fast_group.echelon3"]
})

thinking_wrapper = wrapper_factory.create_task_group_wrapper("thinking_group_wrapper", {
    "target": "thinking_group.echelon1"
})

fast_pool_wrapper = wrapper_factory.create_polling_pool_wrapper("fast_pool_wrapper")

# 注入到LLM节点
llm_node = LLMNode(
    llm_client=default_client,
    task_group_manager=task_group_manager,
    wrapper_factory=wrapper_factory
)
```

## 监控和统计

### 包装器统计信息

```python
# 获取包装器统计
stats = {
    "task_group_wrappers": {},
    "polling_pool_wrappers": {}
}

for name, wrapper in wrapper_factory.list_wrappers().items():
    if isinstance(wrapper, TaskGroupWrapper):
        stats["task_group_wrappers"][name] = {
            "fallback_history": wrapper._fallback_history,
            "current_target": wrapper._current_target,
            "attempt_count": wrapper._attempt_count
        }
    elif isinstance(wrapper, PollingPoolWrapper):
        stats["polling_pool_wrappers"][name] = {
            "rotation_history": wrapper._rotation_history,
            "attempt_count": wrapper._attempt_count,
            "pool_info": wrapper.get_model_info()["pool_info"]
        }
```

## 错误处理

### 包装器错误类型

```python
class WrapperError(LLMError):
    """包装器错误基类"""
    pass

class TaskGroupWrapperError(WrapperError):
    """任务组包装器错误"""
    pass

class PollingPoolWrapperError(WrapperError):
    """轮询池包装器错误"""
    pass

class WrapperFactoryError(WrapperError):
    """包装器工厂错误"""
    pass
```

## 性能优化

### 1. 包装器缓存
- 包装器实例缓存，避免重复创建
- 配置变更时自动更新缓存

### 2. 连接池复用
- 轮询池实例复用，减少创建开销
- 任务组客户端复用

### 3. 异步优化
- 所有包装器方法支持异步
- 降级逻辑异步执行

## 测试策略

### 1. 单元测试
- 包装器功能测试
- 降级逻辑测试
- 错误处理测试

### 2. 集成测试
- LLM节点集成测试
- 工作流集成测试
- 性能测试

### 3. 端到端测试
- 完整工作流测试
- 降级场景测试
- 故障恢复测试

## 总结

这个包装器设计使任务组和轮询池能够直接作为LLM实例供LLM节点使用，提供了统一的接口和丰富的功能，包括降级、监控、统计等。通过包装器工厂模式，可以灵活地创建和管理不同类型的LLM包装器，同时保持向后兼容性。