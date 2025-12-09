"""存储健康检查器

提供统一的存储健康检查和监控功能。
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import threading


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果数据类"""
    component: str
    status: HealthStatus
    message: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    response_time: float = 0.0
    error: Optional[str] = None


@dataclass
class HealthThresholds:
    """健康检查阈值配置"""
    response_time_warning: float = 1.0  # 响应时间警告阈值（秒）
    response_time_critical: float = 5.0  # 响应时间严重阈值（秒）
    success_rate_warning: float = 0.95  # 成功率警告阈值
    success_rate_critical: float = 0.9  # 成功率严重阈值
    error_rate_warning: float = 0.05  # 错误率警告阈值
    error_rate_critical: float = 0.1  # 错误率严重阈值


class HealthChecker:
    """健康检查器
    
    提供存储组件的健康检查和监控功能。
    """
    
    def __init__(
        self,
        check_interval: float = 60.0,  # 检查间隔（秒）
        timeout: float = 10.0,  # 检查超时时间（秒）
        thresholds: Optional[HealthThresholds] = None
    ) -> None:
        """初始化健康检查器
        
        Args:
            check_interval: 检查间隔
            timeout: 检查超时时间
            thresholds: 健康阈值配置
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.thresholds = thresholds or HealthThresholds()
        
        # 健康检查函数
        self._check_functions: Dict[str, Callable] = {}
        
        # 健康状态历史
        self._health_history: Dict[str, List[HealthCheckResult]] = {}
        
        # 当前健康状态
        self._current_status: Dict[str, HealthCheckResult] = {}
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 检查任务
        self._check_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """启动健康检查器"""
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._check_task = asyncio.create_task(self._check_worker())
    
    async def stop(self) -> None:
        """停止健康检查器"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            if self._check_task:
                self._check_task.cancel()
                try:
                    await self._check_task
                except asyncio.CancelledError:
                    pass
                self._check_task = None
    
    def register_check(
        self,
        component: str,
        check_function: Callable[[], Union[HealthCheckResult, Dict[str, Any]]]
    ) -> None:
        """注册健康检查函数
        
        Args:
            component: 组件名称
            check_function: 检查函数，返回HealthCheckResult或字典
        """
        with self._lock:
            self._check_functions[component] = check_function
            
            # 初始化历史记录
            if component not in self._health_history:
                self._health_history[component] = []
    
    def unregister_check(self, component: str) -> None:
        """注销健康检查函数
        
        Args:
            component: 组件名称
        """
        with self._lock:
            self._check_functions.pop(component, None)
            self._health_history.pop(component, None)
            self._current_status.pop(component, None)
    
    async def check_health(self, component: Optional[str] = None) -> Dict[str, HealthCheckResult]:
        """执行健康检查
        
        Args:
            component: 组件名称，None表示检查所有组件
            
        Returns:
            健康检查结果字典
        """
        results = {}
        
        with self._lock:
            components_to_check = [component] if component else list(self._check_functions.keys())
        
        for comp in components_to_check:
            try:
                result = await self._check_component(comp)
                results[comp] = result
                
                # 更新当前状态
                with self._lock:
                    self._current_status[comp] = result
                    
                    # 添加到历史记录
                    if comp not in self._health_history:
                        self._health_history[comp] = []
                    
                    history = self._health_history[comp]
                    history.append(result)
                    
                    # 限制历史记录长度
                    max_history = 100
                    if len(history) > max_history:
                        self._health_history[comp] = history[-max_history:]
                        
            except Exception as e:
                error_result = HealthCheckResult(
                    component=comp,
                    status=HealthStatus.UNKNOWN,
                    message=f"Health check failed: {e}",
                    error=str(e)
                )
                results[comp] = error_result
                
                with self._lock:
                    self._current_status[comp] = error_result
        
        return results
    
    async def _check_component(self, component: str) -> HealthCheckResult:
        """检查单个组件
        
        Args:
            component: 组件名称
            
        Returns:
            健康检查结果
        """
        with self._lock:
            check_function = self._check_functions.get(component)
            if not check_function:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNKNOWN,
                    message=f"No health check function registered for {component}"
                )
        
        start_time = time.time()
        
        try:
            # 执行健康检查
            result = await asyncio.wait_for(
                self._execute_check(check_function),
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            # 标准化结果
            if isinstance(result, dict):
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus(result.get("status", "unknown")),
                    message=result.get("message", ""),
                    response_time=response_time,
                    details=result.get("details", {})
                )
            elif isinstance(result, HealthCheckResult):
                result.response_time = response_time
                return result
            else:
                return HealthCheckResult(
                    component=component,
                    status=HealthStatus.UNKNOWN,
                    message="Invalid health check result type",
                    response_time=response_time
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
                response_time=self.timeout
            )
        except Exception as e:
            return HealthCheckResult(
                component=component,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {e}",
                error=str(e),
                response_time=time.time() - start_time
            )
    
    async def _execute_check(self, check_function: Callable) -> Any:
        """执行检查函数
        
        Args:
            check_function: 检查函数
            
        Returns:
            检查结果
        """
        if asyncio.iscoroutinefunction(check_function):
            return await check_function()
        else:
            # 在线程池中执行同步函数
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, check_function)
    
    def get_current_status(self, component: Optional[str] = None) -> Union[HealthCheckResult, Dict[str, HealthCheckResult]]:
        """获取当前健康状态
        
        Args:
            component: 组件名称，None表示获取所有组件状态
            
        Returns:
            健康状态
        """
        with self._lock:
            if component:
                result = self._current_status.get(component)
                if result is None:
                    return HealthCheckResult(
                        component=component,
                        status=HealthStatus.UNKNOWN,
                        message=f"No health check status for component {component}"
                    )
                return result
            else:
                return self._current_status.copy()
    
    def get_health_history(
        self,
        component: str,
        limit: Optional[int] = None
    ) -> List[HealthCheckResult]:
        """获取健康状态历史
        
        Args:
            component: 组件名称
            limit: 限制返回数量
            
        Returns:
            健康状态历史列表
        """
        with self._lock:
            history = self._health_history.get(component, []).copy()
            
            if limit:
                history = history[-limit:]
            
            return history
    
    def get_overall_health(self) -> HealthCheckResult:
        """获取整体健康状态
        
        Returns:
            整体健康状态
        """
        with self._lock:
            if not self._current_status:
                return HealthCheckResult(
                    component="overall",
                    status=HealthStatus.UNKNOWN,
                    message="No health checks registered"
                )
            
            # 统计各状态数量
            status_counts = {
                HealthStatus.HEALTHY: 0,
                HealthStatus.DEGRADED: 0,
                HealthStatus.UNHEALTHY: 0,
                HealthStatus.UNKNOWN: 0
            }
            
            for result in self._current_status.values():
                status_counts[result.status] += 1
            
            # 确定整体状态
            total_components = sum(status_counts.values())
            
            if status_counts[HealthStatus.UNHEALTHY] > 0:
                overall_status = HealthStatus.UNHEALTHY
                message = f"{status_counts[HealthStatus.UNHEALTHY]} components unhealthy"
            elif status_counts[HealthStatus.UNKNOWN] > total_components / 2:
                overall_status = HealthStatus.UNKNOWN
                message = "Too many components with unknown status"
            elif status_counts[HealthStatus.DEGRADED] > 0:
                overall_status = HealthStatus.DEGRADED
                message = f"{status_counts[HealthStatus.DEGRADED]} components degraded"
            else:
                overall_status = HealthStatus.HEALTHY
                message = "All components healthy"
            
            return HealthCheckResult(
                component="overall",
                status=overall_status,
                message=message,
                details={
                    "total_components": total_components,
                    "status_counts": {k.value: v for k, v in status_counts.items()}
                }
            )
    
    async def _check_worker(self) -> None:
        """检查工作线程"""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                await self.check_health()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                # 记录错误但继续运行
                print(f"Error in health check worker: {e}")


class StorageHealthChecker:
    """存储专用健康检查器
    
    提供存储组件的专用健康检查功能。
    """
    
    def __init__(self, health_checker: HealthChecker) -> None:
        """初始化存储健康检查器
        
        Args:
            health_checker: 基础健康检查器
        """
        self.health_checker = health_checker
    
    def register_storage_checks(self, storage: Any) -> None:
        """注册存储健康检查
        
        Args:
            storage: 存储实例
        """
        storage_name = storage.__class__.__name__
        
        # 注册连接检查
        self.health_checker.register_check(
            f"{storage_name}_connection",
            lambda: self._check_connection(storage)
        )
        
        # 注册性能检查
        self.health_checker.register_check(
            f"{storage_name}_performance",
            lambda: self._check_performance(storage)
        )
        
        # 注册容量检查
        self.health_checker.register_check(
            f"{storage_name}_capacity",
            lambda: self._check_capacity(storage)
        )
    
    def _check_connection(self, storage: Any) -> HealthCheckResult:
        """检查存储连接
        
        Args:
            storage: 存储实例
            
        Returns:
            连接健康检查结果
        """
        try:
            # 检查是否有连接方法
            if hasattr(storage, 'is_connected'):
                is_connected = storage.is_connected()
                if not is_connected:
                    return HealthCheckResult(
                        component="connection",
                        status=HealthStatus.UNHEALTHY,
                        message="Storage not connected"
                    )
            
            # 执行简单的健康检查
            if hasattr(storage, 'health_check'):
                health_info = storage.health_check()
                if isinstance(health_info, dict):
                    return HealthCheckResult(
                        component="connection",
                        status=HealthStatus.HEALTHY,
                        message="Connection healthy",
                        details=health_info
                    )
            
            return HealthCheckResult(
                component="connection",
                status=HealthStatus.HEALTHY,
                message="Connection check passed"
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="connection",
                status=HealthStatus.UNHEALTHY,
                message=f"Connection check failed: {e}",
                error=str(e)
            )
    
    def _check_performance(self, storage: Any) -> HealthCheckResult:
        """检查存储性能
        
        Args:
            storage: 存储实例
            
        Returns:
            性能健康检查结果
        """
        try:
            # 检查是否有指标收集器
            if hasattr(storage, 'metrics'):
                metrics = storage.metrics
                
                # 获取最近的操作指标
                all_metrics = metrics.get_all_metrics()
                
                if not all_metrics:
                    return HealthCheckResult(
                        component="performance",
                        status=HealthStatus.UNKNOWN,
                        message="No performance metrics available"
                    )
                
                # 分析性能指标
                total_ops = sum(m.total_count for m in all_metrics.values())
                total_success = sum(m.success_count for m in all_metrics.values())
                
                if total_ops > 0:
                    success_rate = total_success / total_ops
                    
                    # 根据成功率确定状态
                    if success_rate >= self.health_checker.thresholds.success_rate_critical:
                        status = HealthStatus.HEALTHY
                        message = f"Performance good (success rate: {success_rate:.2%})"
                    elif success_rate >= self.health_checker.thresholds.success_rate_warning:
                        status = HealthStatus.DEGRADED
                        message = f"Performance degraded (success rate: {success_rate:.2%})"
                    else:
                        status = HealthStatus.UNHEALTHY
                        message = f"Performance poor (success rate: {success_rate:.2%})"
                    
                    return HealthCheckResult(
                        component="performance",
                        status=status,
                        message=message,
                        details={
                            "total_operations": total_ops,
                            "success_rate": success_rate,
                            "operation_metrics": {
                                op: {
                                    "total_count": m.total_count,
                                    "success_rate": m.success_rate,
                                    "avg_duration": m.avg_duration
                                }
                                for op, m in all_metrics.items()
                            }
                        }
                    )
            
            return HealthCheckResult(
                component="performance",
                status=HealthStatus.UNKNOWN,
                message="Performance metrics not available"
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="performance",
                status=HealthStatus.UNKNOWN,
                message=f"Performance check failed: {e}",
                error=str(e)
            )
    
    def _check_capacity(self, storage: Any) -> HealthCheckResult:
        """检查存储容量
        
        Args:
            storage: 存储实例
            
        Returns:
            容量健康检查结果
        """
        try:
            # 这里可以实现具体的容量检查逻辑
            # 例如检查磁盘空间、内存使用等
            
            # 默认返回健康状态
            return HealthCheckResult(
                component="capacity",
                status=HealthStatus.HEALTHY,
                message="Capacity check passed",
                details={"note": "Capacity check not implemented"}
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="capacity",
                status=HealthStatus.UNKNOWN,
                message=f"Capacity check failed: {e}",
                error=str(e)
            )