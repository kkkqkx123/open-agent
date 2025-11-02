"""历史管理模块依赖注入配置

提供历史管理相关服务的依赖注入配置。
"""

from typing import Dict, Any
from pathlib import Path

from src.infrastructure.container import IDependencyContainer
from src.domain.history.interfaces import IHistoryManager
from src.domain.history.cost_interfaces import ICostCalculator
from src.domain.history.cost_calculator import CostCalculator
from src.application.history.manager import HistoryManager
from src.application.history.token_tracker import TokenUsageTracker
from src.infrastructure.history.storage.file_storage import FileHistoryStorage
from src.infrastructure.history.history_hook import HistoryRecordingHook
from src.infrastructure.llm.token_calculators.base import ITokenCalculator
from src.infrastructure.llm.interfaces import ILLMCallHook


def register_history_services(container: IDependencyContainer, config: Dict[str, Any]) -> None:
    """注册历史管理相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    history_config = config.get("history", {})
    
    # 检查是否启用历史存储
    if not history_config.get("enabled", False):
        return
    
    # 注册存储
    storage_path = Path(history_config.get("storage_path", "./history"))
    container.register_instance(
        FileHistoryStorage,
        FileHistoryStorage(storage_path)
    )
    
    # 注册管理器
    container.register(
        IHistoryManager,
        HistoryManager,
        lifetime="singleton"
    )
    
    # 注册成本计算器
    pricing_config = history_config.get("pricing", {})
    container.register_instance(
        ICostCalculator,
        CostCalculator(pricing_config)
    )


def register_history_services_with_dependencies(
    container: IDependencyContainer,
    config: Dict[str, Any],
    token_calculator: ITokenCalculator
) -> None:
    """注册历史管理相关服务（带依赖）
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        token_calculator: Token计算器实例
    """
    history_config = config.get("history", {})
    
    # 检查是否启用历史存储
    if not history_config.get("enabled", False):
        return
    
    # 注册存储
    storage_path = Path(history_config.get("storage_path", "./history"))
    container.register_instance(
        FileHistoryStorage,
        FileHistoryStorage(storage_path)
    )
    
    # 注册管理器
    container.register(
        IHistoryManager,
        HistoryManager,
        lifetime="singleton"
    )
    
    # 注册成本计算器
    pricing_config = history_config.get("pricing", {})
    container.register_instance(
        ICostCalculator,
        CostCalculator(pricing_config)
    )
    
    # 注册Token使用追踪器（依赖Token计算器）
    container.register_factory(
        TokenUsageTracker,
        lambda: TokenUsageTracker(
            token_counter=token_calculator,
            history_manager=container.get(IHistoryManager)
        ),
        lifetime="singleton"
    )
    
    # 注册历史记录钩子（依赖多个服务）
    container.register_factory(
        HistoryRecordingHook,
        lambda: HistoryRecordingHook(
            history_manager=container.get(IHistoryManager),
            token_tracker=container.get(TokenUsageTracker),
            cost_calculator=container.get(ICostCalculator)
        ),
        lifetime="singleton"
    )
    
    # 将历史记录钩子注册为ILLMCallHook接口
    container.register_factory(
        ILLMCallHook,
        lambda: container.get(HistoryRecordingHook),
        lifetime="singleton"
    )


def register_test_history_services(container: IDependencyContainer) -> None:
    """注册测试环境的历史管理服务
    
    Args:
        container: 依赖注入容器
    """
    # 使用内存存储进行测试
    from src.infrastructure.history.storage.memory_storage import MemoryHistoryStorage
    
    container.register_instance(
        FileHistoryStorage,
        MemoryHistoryStorage()
    )
    
    # 注册管理器
    container.register(
        IHistoryManager,
        HistoryManager,
        lifetime="singleton"
    )
    
    # 注册成本计算器（使用测试定价）
    test_pricing = {
        "openai:gpt-4": {
            "prompt_price_per_1k": 0.01,
            "completion_price_per_1k": 0.03
        },
        "openai:gpt-3.5-turbo": {
            "prompt_price_per_1k": 0.001,
            "completion_price_per_1k": 0.002
        }
    }
    container.register_instance(
        ICostCalculator,
        CostCalculator(test_pricing)
    )
    
    # 注册Token使用追踪器（测试版本，不需要依赖）
    # 注意：实际使用时需要通过register_history_services_with_dependencies注册
    
    # 注册历史记录钩子
    container.register(
        ILLMCallHook,
        HistoryRecordingHook,
        lifetime="singleton"
    )