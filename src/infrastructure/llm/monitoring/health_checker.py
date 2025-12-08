"""健康检查器基础设施模块

提供统一的健康检查功能。
"""

import time
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Awaitable
from enum import Enum


class HealthStatus(Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    
    status: HealthStatus
    message: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    duration: Optional[float] = None
    check_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
            "duration": self.duration,
            "check_name": self.check_name,
        }


class HealthCheck:
    """健康检查基类"""
    
    def __init__(self, name: str, timeout: float = 10.0):
        """
        初始化健康检查
        
        Args:
            name: 检查名称
            timeout: 超时时间（秒）
        """
        self.name = name
        self.timeout = timeout
    
    async def check_async(self) -> HealthCheckResult:
        """
        执行异步健康检查
        
        Returns:
            健康检查结果
        """
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(self._do_check_async(), timeout=self.timeout)
            result.duration = time.time() - start_time
            result.check_name = self.name
            return result
        except asyncio.TimeoutError:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"健康检查超时: {self.timeout}秒",
                duration=time.time() - start_time,
                check_name=self.name
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"健康检查失败: {str(e)}",
                duration=time.time() - start_time,
                check_name=self.name,
                details={"error": str(e), "error_type": type(e).__name__}
            )
    
    def check(self) -> HealthCheckResult:
        """
        执行同步健康检查
        
        Returns:
            健康检查结果
        """
        start_time = time.time()
        
        try:
            result = self._do_check()
            result.duration = time.time() - start_time
            result.check_name = self.name
            return result
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"健康检查失败: {str(e)}",
                duration=time.time() - start_time,
                check_name=self.name,
                details={"error": str(e), "error_type": type(e).__name__}
            )
    
    async def _do_check_async(self) -> HealthCheckResult:
        """执行异步检查逻辑（子类实现）"""
        return await asyncio.get_event_loop().run_in_executor(None, self._do_check)
    
    def _do_check(self) -> HealthCheckResult:
        """执行检查逻辑（子类实现）"""
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="健康检查通过"
        )


class FunctionHealthCheck(HealthCheck):
    """基于函数的健康检查"""
    
    def __init__(self, name: str, check_func: Callable[[], Any], timeout: float = 10.0):
        """
        初始化函数健康检查
        
        Args:
            name: 检查名称
            check_func: 检查函数
            timeout: 超时时间（秒）
        """
        super().__init__(name, timeout)
        self.check_func = check_func
    
    def _do_check(self) -> HealthCheckResult:
        """执行函数检查"""
        try:
            result = self.check_func()
            
            # 如果返回的是HealthCheckResult，直接使用
            if isinstance(result, HealthCheckResult):
                return result
            
            # 如果返回的是布尔值
            if isinstance(result, bool):
                if result:
                    return HealthCheckResult(
                        status=HealthStatus.HEALTHY,
                        message="函数检查通过"
                    )
                else:
                    return HealthCheckResult(
                        status=HealthStatus.UNHEALTHY,
                        message="函数检查失败"
                    )
            
            # 其他情况认为健康
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="函数检查通过",
                details={"result": result}
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"函数检查异常: {str(e)}",
                details={"error": str(e)}
            )


class AsyncFunctionHealthCheck(HealthCheck):
    """基于异步函数的健康检查"""
    
    def __init__(self, name: str, check_func: Callable[[], Awaitable[Any]], timeout: float = 10.0):
        """
        初始化异步函数健康检查
        
        Args:
            name: 检查名称
            check_func: 异步检查函数
            timeout: 超时时间（秒）
        """
        super().__init__(name, timeout)
        self.check_func = check_func
    
    async def _do_check_async(self) -> HealthCheckResult:
        """执行异步函数检查"""
        try:
            result = await self.check_func()
            
            # 如果返回的是HealthCheckResult，直接使用
            if isinstance(result, HealthCheckResult):
                return result
            
            # 如果返回的是布尔值
            if isinstance(result, bool):
                if result:
                    return HealthCheckResult(
                        status=HealthStatus.HEALTHY,
                        message="异步函数检查通过"
                    )
                else:
                    return HealthCheckResult(
                        status=HealthStatus.UNHEALTHY,
                        message="异步函数检查失败"
                    )
            
            # 其他情况认为健康
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="异步函数检查通过",
                details={"result": result}
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"异步函数检查异常: {str(e)}",
                details={"error": str(e)}
            )


class HTTPHealthCheck(HealthCheck):
    """HTTP健康检查"""
    
    def __init__(self, name: str, url: str, timeout: float = 10.0, expected_status: int = 200):
        """
        初始化HTTP健康检查
        
        Args:
            name: 检查名称
            url: 检查URL
            timeout: 超时时间（秒）
            expected_status: 期望的HTTP状态码
        """
        super().__init__(name, timeout)
        self.url = url
        self.expected_status = expected_status
    
    async def _do_check_async(self) -> HealthCheckResult:
        """执行HTTP检查"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(self.url) as response:
                    if response.status == self.expected_status:
                        return HealthCheckResult(
                            status=HealthStatus.HEALTHY,
                            message=f"HTTP检查通过: {response.status}",
                            details={
                                "url": self.url,
                                "status_code": response.status,
                                "expected_status": self.expected_status
                            }
                        )
                    else:
                        return HealthCheckResult(
                            status=HealthStatus.UNHEALTHY,
                            message=f"HTTP状态码不匹配: {response.status} != {self.expected_status}",
                            details={
                                "url": self.url,
                                "status_code": response.status,
                                "expected_status": self.expected_status
                            }
                        )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"HTTP检查失败: {str(e)}",
                details={"url": self.url, "error": str(e)}
            )


class HealthChecker:
    """健康检查器
    
    提供统一的健康检查功能。
    """
    
    def __init__(self):
        """初始化健康检查器"""
        self._checks: Dict[str, HealthCheck] = {}
        self._last_results: Dict[str, HealthCheckResult] = {}
    
    def register_check(self, check: HealthCheck) -> None:
        """
        注册健康检查
        
        Args:
            check: 健康检查对象
        """
        self._checks[check.name] = check
    
    def unregister_check(self, name: str) -> None:
        """
        注销健康检查
        
        Args:
            name: 检查名称
        """
        if name in self._checks:
            del self._checks[name]
        if name in self._last_results:
            del self._last_results[name]
    
    async def check_all_async(self) -> Dict[str, HealthCheckResult]:
        """
        执行所有异步健康检查
        
        Returns:
            所有检查结果字典
        """
        results = {}
        
        # 并行执行所有检查
        tasks = []
        check_names = []
        
        for name, check in self._checks.items():
            tasks.append(check.check_async())
            check_names.append(name)
        
        if tasks:
            check_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for name, result in zip(check_names, check_results):
                if isinstance(result, Exception):
                    error_result = HealthCheckResult(
                        status=HealthStatus.UNHEALTHY,
                        message=f"检查执行异常: {str(result)}",
                        check_name=name,
                        details={"error": str(result)}
                    )
                    results[name] = error_result
                    self._last_results[name] = error_result
                else:
                    # 明确类型断言，确保result是HealthCheckResult类型
                    health_result: HealthCheckResult = result  # type: ignore
                    results[name] = health_result
                    self._last_results[name] = health_result
        
        return results
    
    def check_all(self) -> Dict[str, HealthCheckResult]:
        """
        执行所有同步健康检查
        
        Returns:
            所有检查结果字典
        """
        results = {}
        
        for name, check in self._checks.items():
            try:
                result = check.check()
                results[name] = result
                self._last_results[name] = result
            except Exception as e:
                results[name] = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"检查执行异常: {str(e)}",
                    check_name=name,
                    details={"error": str(e)}
                )
        
        return results
    
    async def check_async(self, name: str) -> HealthCheckResult:
        """
        执行指定的异步健康检查
        
        Args:
            name: 检查名称
            
        Returns:
            检查结果
        """
        if name not in self._checks:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"健康检查不存在: {name}",
                check_name=name
            )
        
        result = await self._checks[name].check_async()
        self._last_results[name] = result
        return result
    
    def check(self, name: str) -> HealthCheckResult:
        """
        执行指定的同步健康检查
        
        Args:
            name: 检查名称
            
        Returns:
            检查结果
        """
        if name not in self._checks:
            return HealthCheckResult(
                status=HealthStatus.UNKNOWN,
                message=f"健康检查不存在: {name}",
                check_name=name
            )
        
        result = self._checks[name].check()
        self._last_results[name] = result
        return result
    
    def get_overall_health(self) -> HealthStatus:
        """
        获取整体健康状态
        
        Returns:
            整体健康状态
        """
        if not self._last_results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in self._last_results.values()]
        
        # 如果有任何不健康的检查，整体状态为不健康
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        
        # 如果有任何降级的检查，整体状态为降级
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        # 如果有未知状态的检查，整体状态为未知
        if HealthStatus.UNKNOWN in statuses:
            return HealthStatus.UNKNOWN
        
        # 否则为健康
        return HealthStatus.HEALTHY
    
    def get_last_results(self) -> Dict[str, HealthCheckResult]:
        """
        获取最后的检查结果
        
        Returns:
            最后的检查结果字典
        """
        return self._last_results.copy()
    
    def get_check_names(self) -> List[str]:
        """
        获取所有检查名称
        
        Returns:
            检查名称列表
        """
        return list(self._checks.keys())
    
    def clear_results(self) -> None:
        """清空检查结果"""
        self._last_results.clear()


class HealthCheckerFactory:
    """健康检查器工厂"""
    
    @staticmethod
    def create_default() -> HealthChecker:
        """创建默认健康检查器"""
        return HealthChecker()
    
    @staticmethod
    def create_function_check(name: str, func: Callable[[], Any], timeout: float = 10.0) -> FunctionHealthCheck:
        """创建函数健康检查"""
        return FunctionHealthCheck(name, func, timeout)
    
    @staticmethod
    def create_async_function_check(name: str, func: Callable[[], Awaitable[Any]], timeout: float = 10.0) -> AsyncFunctionHealthCheck:
        """创建异步函数健康检查"""
        return AsyncFunctionHealthCheck(name, func, timeout)
    
    @staticmethod
    def create_http_check(name: str, url: str, timeout: float = 10.0, expected_status: int = 200) -> HTTPHealthCheck:
        """创建HTTP健康检查"""
        return HTTPHealthCheck(name, url, timeout, expected_status)