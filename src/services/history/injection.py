"""History依赖注入便利层

使用通用依赖注入框架提供简洁的History服务获取方式。
"""

from typing import Optional

from src.interfaces.history import IHistoryManager, ICostCalculator
from src.core.history.interfaces import ITokenTracker
from src.interfaces.repository.history import IHistoryRepository
from src.services.history.statistics_service import HistoryStatisticsService
from src.services.history.hooks import HistoryRecordingHook
from src.services.llm.token_calculation_service import TokenCalculationService
from src.services.llm.token_calculation_decorator import TokenCalculationDecorator
from src.services.container.injection.injection_base import get_global_injection_registry
from src.services.container.injection.injection_decorators import injectable


class _StubHistoryManager(IHistoryManager):
    """临时 HistoryManager 实现（用于极端情况）
    
    当 HistoryManager 初始化失败时使用此实现，确保代码不会因为
    缺少 HistoryManager 而直接崩溃。
    """
    
    def __init__(self):
        self._storage = None
    
    def record_event(self, event_data: dict) -> str:
        """记录事件"""
        return "stub_event_id"
    
    def get_events(self, session_id: str, limit: Optional[int] = None) -> list:
        """获取事件列表"""
        return []
    
    def get_event(self, event_id: str) -> Optional[dict]:
        """获取单个事件"""
        return None
    
    def delete_events(self, session_id: str) -> int:
        """删除会话事件"""
        return 0


class _StubCostCalculator(ICostCalculator):
    """临时 CostCalculator 实现（用于极端情况）"""
    
    def calculate_cost(self, tokens: int, model: str) -> float:
        """计算成本"""
        return 0.0
    
    def get_pricing_info(self, model: str) -> dict:
        """获取定价信息"""
        return {"input_price": 0.0, "output_price": 0.0}


class _StubTokenTracker(ITokenTracker):
    """临时 TokenTracker 实现（用于极端情况）"""
    
    def track_tokens(self, tokens: int, model: str, session_id: str) -> None:
        """追踪Token使用"""
        pass
    
    def get_token_usage(self, session_id: str) -> dict:
        """获取Token使用情况"""
        return {"total_tokens": 0, "total_cost": 0.0}


class _StubHistoryRepository(IHistoryRepository):
    """临时 HistoryRepository 实现（用于极端情况）"""
    
    def save(self, data: dict) -> str:
        """保存数据"""
        return "stub_id"
    
    def load(self, id: str) -> Optional[dict]:
        """加载数据"""
        return None
    
    def delete(self, id: str) -> bool:
        """删除数据"""
        return False


class _StubStatisticsService(HistoryStatisticsService):
    """临时 StatisticsService 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def get_usage_stats(self, session_id: str) -> dict:
        """获取使用统计"""
        return {"total_events": 0, "total_tokens": 0}
    
    def get_cost_stats(self, session_id: str) -> dict:
        """获取成本统计"""
        return {"total_cost": 0.0}


class _StubHistoryHooks(HistoryRecordingHook):
    """临时 HistoryHooks 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def before_execution(self, context: dict) -> None:
        """执行前钩子"""
        pass
    
    def after_execution(self, context: dict, result: any) -> None:
        """执行后钩子"""
        pass


class _StubTokenCalculationService(TokenCalculationService):
    """临时 TokenCalculationService 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def count_tokens(self, text: str, model: str) -> int:
        """计算Token数量"""
        return len(text.split())
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """估算成本"""
        return 0.0


class _StubTokenCalculationDecorator(TokenCalculationDecorator):
    """临时 TokenCalculationDecorator 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def count_tokens(self, text: str, model: str) -> int:
        """计算Token数量"""
        return len(text.split())
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """估算成本"""
        return 0.0


def _create_fallback_history_manager() -> IHistoryManager:
    """创建fallback history manager"""
    return _StubHistoryManager()


def _create_fallback_cost_calculator() -> ICostCalculator:
    """创建fallback cost calculator"""
    return _StubCostCalculator()


def _create_fallback_token_tracker() -> ITokenTracker:
    """创建fallback token tracker"""
    return _StubTokenTracker()


def _create_fallback_history_repository() -> IHistoryRepository:
    """创建fallback history repository"""
    return _StubHistoryRepository()


def _create_fallback_statistics_service() -> HistoryStatisticsService:
    """创建fallback statistics service"""
    return _StubStatisticsService()


def _create_fallback_history_hooks() -> HistoryRecordingHook:
    """创建fallback history hooks"""
    return _StubHistoryHooks()


def _create_fallback_token_calculation_service() -> TokenCalculationService:
    """创建fallback token calculation service"""
    return _StubTokenCalculationService()


def _create_fallback_token_calculation_decorator() -> TokenCalculationDecorator:
    """创建fallback token calculation decorator"""
    return _StubTokenCalculationDecorator()


# 注册History注入
_history_manager_injection = get_global_injection_registry().register(
    IHistoryManager, _create_fallback_history_manager
)
_cost_calculator_injection = get_global_injection_registry().register(
    ICostCalculator, _create_fallback_cost_calculator
)
_token_tracker_injection = get_global_injection_registry().register(
    ITokenTracker, _create_fallback_token_tracker
)
_history_repository_injection = get_global_injection_registry().register(
    IHistoryRepository, _create_fallback_history_repository
)
_statistics_service_injection = get_global_injection_registry().register(
    HistoryStatisticsService, _create_fallback_statistics_service
)
_history_hooks_injection = get_global_injection_registry().register(
    HistoryRecordingHook, _create_fallback_history_hooks
)
_token_calculation_service_injection = get_global_injection_registry().register(
    TokenCalculationService, _create_fallback_token_calculation_service
)
_token_calculation_decorator_injection = get_global_injection_registry().register(
    TokenCalculationDecorator, _create_fallback_token_calculation_decorator
)


@injectable(IHistoryManager, _create_fallback_history_manager)
def get_history_manager() -> IHistoryManager:
    """获取History管理器实例
    
    获取策略（按优先级）：
    1. 使用全局 HistoryManager 实例（由容器设置）
    2. 尝试从容器获取
    3. 降级到临时实现（防止崩溃）
    
    Returns:
        IHistoryManager: History管理器实例
        
    Example:
        ```python
        # 获取History管理器
        history_manager = get_history_manager()
        
        # 记录事件
        event_id = history_manager.record_event({
            "type": "user_action",
            "data": {"action": "login"}
        })
        ```
    """
    return _history_manager_injection.get_instance()


@injectable(ICostCalculator, _create_fallback_cost_calculator)
def get_cost_calculator() -> ICostCalculator:
    """获取成本计算器实例
    
    Returns:
        ICostCalculator: 成本计算器实例
    """
    return _cost_calculator_injection.get_instance()


@injectable(ITokenTracker, _create_fallback_token_tracker)
def get_token_tracker() -> ITokenTracker:
    """获取Token追踪器实例
    
    Returns:
        ITokenTracker: Token追踪器实例
    """
    return _token_tracker_injection.get_instance()


@injectable(IHistoryRepository, _create_fallback_history_repository)
def get_history_repository() -> IHistoryRepository:
    """获取History仓储实例
    
    Returns:
        IHistoryRepository: History仓储实例
    """
    return _history_repository_injection.get_instance()


@injectable(HistoryStatisticsService, _create_fallback_statistics_service)
def get_statistics_service() -> HistoryStatisticsService:
    """获取统计服务实例
    
    Returns:
        HistoryStatisticsService: 统计服务实例
    """
    return _statistics_service_injection.get_instance()


@injectable(HistoryRecordingHook, _create_fallback_history_hooks)
def get_history_hooks() -> HistoryRecordingHook:
    """获取History钩子实例
    
    Returns:
        HistoryRecordingHook: History钩子实例
    """
    return _history_hooks_injection.get_instance()


@injectable(TokenCalculationService, _create_fallback_token_calculation_service)
def get_token_calculation_service() -> TokenCalculationService:
    """获取Token计算服务实例
    
    Returns:
        TokenCalculationService: Token计算服务实例
    """
    return _token_calculation_service_injection.get_instance()


@injectable(TokenCalculationDecorator, _create_fallback_token_calculation_decorator)
def get_token_calculation_decorator() -> TokenCalculationDecorator:
    """获取Token计算装饰器实例
    
    Returns:
        TokenCalculationDecorator: Token计算装饰器实例
    """
    return _token_calculation_decorator_injection.get_instance()


# 设置实例的函数
def set_history_manager_instance(history_manager: IHistoryManager) -> None:
    """在应用启动时设置全局 HistoryManager 实例
    
    Args:
        history_manager: IHistoryManager 实例
    """
    _history_manager_injection.set_instance(history_manager)


def set_cost_calculator_instance(cost_calculator: ICostCalculator) -> None:
    """在应用启动时设置全局 CostCalculator 实例
    
    Args:
        cost_calculator: ICostCalculator 实例
    """
    _cost_calculator_injection.set_instance(cost_calculator)


def set_token_tracker_instance(token_tracker: ITokenTracker) -> None:
    """在应用启动时设置全局 TokenTracker 实例
    
    Args:
        token_tracker: ITokenTracker 实例
    """
    _token_tracker_injection.set_instance(token_tracker)


def set_history_repository_instance(history_repository: IHistoryRepository) -> None:
    """在应用启动时设置全局 HistoryRepository 实例
    
    Args:
        history_repository: IHistoryRepository 实例
    """
    _history_repository_injection.set_instance(history_repository)


def set_statistics_service_instance(statistics_service: HistoryStatisticsService) -> None:
    """在应用启动时设置全局 StatisticsService 实例
    
    Args:
        statistics_service: HistoryStatisticsService 实例
    """
    _statistics_service_injection.set_instance(statistics_service)


def set_history_hooks_instance(history_hooks: HistoryRecordingHook) -> None:
    """在应用启动时设置全局 HistoryHooks 实例
    
    Args:
        history_hooks: HistoryRecordingHook 实例
    """
    _history_hooks_injection.set_instance(history_hooks)


def set_token_calculation_service_instance(token_calculation_service: TokenCalculationService) -> None:
    """在应用启动时设置全局 TokenCalculationService 实例
    
    Args:
        token_calculation_service: TokenCalculationService 实例
    """
    _token_calculation_service_injection.set_instance(token_calculation_service)


def set_token_calculation_decorator_instance(token_calculation_decorator: TokenCalculationDecorator) -> None:
    """在应用启动时设置全局 TokenCalculationDecorator 实例
    
    Args:
        token_calculation_decorator: TokenCalculationDecorator 实例
    """
    _token_calculation_decorator_injection.set_instance(token_calculation_decorator)


# 清除实例的函数
def clear_history_manager_instance() -> None:
    """清除全局 HistoryManager 实例"""
    _history_manager_injection.clear_instance()


def clear_cost_calculator_instance() -> None:
    """清除全局 CostCalculator 实例"""
    _cost_calculator_injection.clear_instance()


def clear_token_tracker_instance() -> None:
    """清除全局 TokenTracker 实例"""
    _token_tracker_injection.clear_instance()


def clear_history_repository_instance() -> None:
    """清除全局 HistoryRepository 实例"""
    _history_repository_injection.clear_instance()


def clear_statistics_service_instance() -> None:
    """清除全局 StatisticsService 实例"""
    _statistics_service_injection.clear_instance()


def clear_history_hooks_instance() -> None:
    """清除全局 HistoryHooks 实例"""
    _history_hooks_injection.clear_instance()


def clear_token_calculation_service_instance() -> None:
    """清除全局 TokenCalculationService 实例"""
    _token_calculation_service_injection.clear_instance()


def clear_token_calculation_decorator_instance() -> None:
    """清除全局 TokenCalculationDecorator 实例"""
    _token_calculation_decorator_injection.clear_instance()


# 获取状态的函数
def get_history_manager_status() -> dict:
    """获取History管理器注入状态"""
    return _history_manager_injection.get_status()


def get_cost_calculator_status() -> dict:
    """获取成本计算器注入状态"""
    return _cost_calculator_injection.get_status()


def get_token_tracker_status() -> dict:
    """获取Token追踪器注入状态"""
    return _token_tracker_injection.get_status()


def get_history_repository_status() -> dict:
    """获取History仓储注入状态"""
    return _history_repository_injection.get_status()


def get_statistics_service_status() -> dict:
    """获取统计服务注入状态"""
    return _statistics_service_injection.get_status()


def get_history_hooks_status() -> dict:
    """获取History钩子注入状态"""
    return _history_hooks_injection.get_status()


def get_token_calculation_service_status() -> dict:
    """获取Token计算服务注入状态"""
    return _token_calculation_service_injection.get_status()


def get_token_calculation_decorator_status() -> dict:
    """获取Token计算装饰器注入状态"""
    return _token_calculation_decorator_injection.get_status()


# 导出的公共接口
__all__ = [
    "get_history_manager",
    "get_cost_calculator",
    "get_token_tracker",
    "get_history_repository",
    "get_statistics_service",
    "get_history_hooks",
    "get_token_calculation_service",
    "get_token_calculation_decorator",
    "set_history_manager_instance",
    "set_cost_calculator_instance",
    "set_token_tracker_instance",
    "set_history_repository_instance",
    "set_statistics_service_instance",
    "set_history_hooks_instance",
    "set_token_calculation_service_instance",
    "set_token_calculation_decorator_instance",
    "clear_history_manager_instance",
    "clear_cost_calculator_instance",
    "clear_token_tracker_instance",
    "clear_history_repository_instance",
    "clear_statistics_service_instance",
    "clear_history_hooks_instance",
    "clear_token_calculation_service_instance",
    "clear_token_calculation_decorator_instance",
    "get_history_manager_status",
    "get_cost_calculator_status",
    "get_token_tracker_status",
    "get_history_repository_status",
    "get_statistics_service_status",
    "get_history_hooks_status",
    "get_token_calculation_service_status",
    "get_token_calculation_decorator_status",
]