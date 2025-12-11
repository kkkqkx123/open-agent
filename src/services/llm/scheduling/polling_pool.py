"""LLM轮询池实现"""

import asyncio
import time
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random

from .concurrency_controller import ConcurrencyAndRateLimitManager, ConcurrencyLevel
from .task_group_manager import TaskGroupManager
from src.interfaces.llm import IPollingPoolManager
from src.interfaces.llm import ILLMClient
from src.interfaces.llm.exceptions import LLMError

logger = get_logger(__name__)


class InstanceStatus(Enum):
    """实例状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"
    RECOVERING = "recovering"


class RotationStrategy(Enum):
    """轮询策略"""
    ROUND_ROBIN = "round_robin"
    LEAST_RECENTLY_USED = "least_recently_used"
    WEIGHTED = "weighted"


@dataclass
class LLMInstance:
    """LLM实例信息"""
    instance_id: str
    model_name: str
    group_name: str
    echelon: str
    client: Optional[ILLMClient] = None
    status: InstanceStatus = InstanceStatus.HEALTHY
    last_health_check: datetime = field(default_factory=datetime.now)
    failure_count: int = 0
    success_count: int = 0
    avg_response_time: float = 0.0
    current_load: int = 0
    max_concurrency: int = 10
    weight: float = 1.0
    last_used: Optional[datetime] = None
    
    def is_available(self) -> bool:
        """检查实例是否可用"""
        return self.status in [InstanceStatus.HEALTHY, InstanceStatus.DEGRADED]
    
    def can_accept_request(self) -> bool:
        """检查实例是否能接受新请求"""
        return (self.is_available() and 
                self.current_load < self.max_concurrency)
    
    def update_performance(self, response_time: float, success: bool) -> None:
        """更新性能指标"""
        if success:
            self.success_count += 1
            # 更新平均响应时间
            total_requests = self.success_count + self.failure_count
            if total_requests == 1:
                self.avg_response_time = response_time
            else:
                self.avg_response_time = (
                    (self.avg_response_time * (total_requests - 1) + response_time) / total_requests
                )
        else:
            self.failure_count += 1
        
        self.last_used = datetime.now()


class Scheduler:
    """调度器基类"""
    
    def select_instance(self, instances: List[LLMInstance]) -> Optional[LLMInstance]:
        """选择实例"""
        raise NotImplementedError


class RoundRobinScheduler(Scheduler):
    """轮询调度器"""
    
    def __init__(self):
        self.current_index = 0
    
    def select_instance(self, instances: List[LLMInstance]) -> Optional[LLMInstance]:
        """选择下一个实例"""
        available_instances = [inst for inst in instances if inst.can_accept_request()]
        
        if not available_instances:
            return None
        
        selected = available_instances[self.current_index % len(available_instances)]
        self.current_index += 1
        
        return selected


class LeastRecentlyUsedScheduler(Scheduler):
    """最少使用调度器"""
    
    def select_instance(self, instances: List[LLMInstance]) -> Optional[LLMInstance]:
        """选择最少使用的实例"""
        available_instances = [inst for inst in instances if inst.can_accept_request()]
        
        if not available_instances:
            return None
        
        # 找到最少使用的实例
        selected = min(available_instances, 
                      key=lambda inst: inst.last_used or datetime.min)
        
        return selected


class WeightedScheduler(Scheduler):
    """加权调度器"""
    
    def calculate_weight(self, instance: LLMInstance) -> float:
        """计算实例权重"""
        base_weight = instance.weight
        
        # 根据性能调整权重
        if instance.avg_response_time > 0:
            performance_weight = 1.0 / instance.avg_response_time
        else:
            performance_weight = 1.0
        
        # 根据成功率调整权重
        total_requests = instance.success_count + instance.failure_count
        if total_requests > 0:
            success_rate = instance.success_count / total_requests
            reliability_weight = success_rate
        else:
            reliability_weight = 1.0
        
        # 根据当前负载调整权重
        load_weight = 1.0 - (instance.current_load / instance.max_concurrency)
        
        # 综合权重
        final_weight = base_weight * performance_weight * reliability_weight * load_weight
        
        return max(final_weight, 0.1)  # 最小权重
    
    def select_instance(self, instances: List[LLMInstance]) -> Optional[LLMInstance]:
        """根据权重选择实例"""
        available_instances = [inst for inst in instances if inst.can_accept_request()]
        
        if not available_instances:
            return None
        
        # 计算权重并选择
        weights = [self.calculate_weight(inst) for inst in available_instances]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return available_instances[0]
        
        # 加权随机选择
        rand_value = random.uniform(0, total_weight)
        current_weight = 0
        
        for i, weight in enumerate(weights):
            current_weight += weight
            if rand_value <= current_weight:
                return available_instances[i]
        
        return available_instances[-1]


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.running = False
    
    async def start(self, instances: List[LLMInstance], 
                   health_check_callback: Optional[Callable] = None) -> None:
        """启动健康检查"""
        self.running = True
        
        while self.running:
            await self._check_instances(instances, health_check_callback)
            await asyncio.sleep(self.check_interval)
    
    def stop(self) -> None:
        """停止健康检查"""
        self.running = False
    
    async def _check_instances(self, instances: List[LLMInstance], 
                             health_check_callback: Optional[Callable] = None) -> None:
        """检查所有实例"""
        tasks = [self._check_instance(instance, health_check_callback) for instance in instances]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_instance(self, instance: LLMInstance, 
                            health_check_callback: Optional[Callable] = None) -> None:
        """检查单个实例"""
        try:
            # 执行健康检查
            is_healthy = await self._perform_health_check(instance)
            
            if is_healthy:
                if instance.status == InstanceStatus.FAILED:
                    instance.status = InstanceStatus.RECOVERING
                elif instance.status == InstanceStatus.RECOVERING:
                    instance.status = InstanceStatus.HEALTHY
                
                instance.failure_count = 0
            else:
                instance.failure_count += 1
                
                if instance.failure_count >= 3:
                    instance.status = InstanceStatus.FAILED
                elif instance.status == InstanceStatus.HEALTHY:
                    instance.status = InstanceStatus.DEGRADED
            
            instance.last_health_check = datetime.now()
            
            # 调用回调
            if health_check_callback:
                health_check_callback(instance)
            
        except Exception as e:
            logger.error(f"健康检查失败 {instance.instance_id}: {e}")
            instance.failure_count += 1
            if instance.failure_count >= 3:
                instance.status = InstanceStatus.FAILED
    
    async def _perform_health_check(self, instance: LLMInstance) -> bool:
        """执行具体的健康检查"""
        try:
            # 发送简单的ping请求
            # 这里可以实现具体的健康检查逻辑
            await asyncio.sleep(0.1)  # 模拟网络延迟
            return True
        except:
            return False


class PollingPool:
    """轮询池"""
    
    def __init__(self, 
                 name: str,
                 config: Dict[str, Any],
                 task_group_manager: TaskGroupManager):
        """
        初始化轮询池
        
        Args:
            name: 轮询池名称
            config: 轮询池配置
            task_group_manager: 任务组管理器
        """
        self.name = name
        self.config = config
        self.task_group_manager = task_group_manager
        self.instances: List[LLMInstance] = []
        self.scheduler = self._create_scheduler()
        self.health_checker = HealthChecker(config.get("health_check_interval", 30))
        self.concurrency_manager = self._create_concurrency_manager()
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0
        }
    
    def _create_scheduler(self) -> Scheduler:
        """创建调度器"""
        strategy = RotationStrategy(self.config.get("rotation_strategy", "round_robin"))
        
        if strategy == RotationStrategy.ROUND_ROBIN:
            return RoundRobinScheduler()
        elif strategy == RotationStrategy.LEAST_RECENTLY_USED:
            return LeastRecentlyUsedScheduler()
        elif strategy == RotationStrategy.WEIGHTED:
            return WeightedScheduler()
        else:
            raise ValueError(f"不支持的调度策略: {strategy}")
    
    def _create_concurrency_manager(self) -> ConcurrencyAndRateLimitManager:
        """创建并发管理器"""
        concurrency_config = self.config.get("concurrency_control", {"enabled": False})
        rate_limit_config = self.config.get("rate_limiting", {"enabled": False})
        
        return ConcurrencyAndRateLimitManager(concurrency_config, rate_limit_config)
    
    async def initialize(self) -> None:
        """初始化轮询池"""
        # 从任务组配置创建实例
        task_groups = self.config.get("task_groups", [])
        
        for task_group_ref in task_groups:
            await self._create_instances_from_task_group(task_group_ref)
        
        # 启动健康检查
        asyncio.create_task(self.health_checker.start(self.instances))
        
        logger.info(f"轮询池 {self.name} 初始化完成，共 {len(self.instances)} 个实例")
    
    async def _create_instances_from_task_group(self, task_group_ref: str) -> None:
        """从任务组创建实例"""
        try:
            models = self.task_group_manager.get_models_for_group(task_group_ref)
            
            for model_name in models:
                # TODO: 这里应该根据模型名称创建实际的LLM客户端
                # 暂时创建模拟实例
                instance = LLMInstance(
                    instance_id=f"{task_group_ref}_{model_name}",
                    model_name=model_name,
                    group_name=task_group_ref.split(".")[0],
                    echelon=task_group_ref.split(".")[1] if "." in task_group_ref else "default",
                    client=None
                )
                self.instances.append(instance)
                
        except Exception as e:
            logger.error(f"从任务组 {task_group_ref} 创建实例失败: {e}")
    
    async def get_instance(self) -> Optional[LLMInstance]:
        """获取可用实例"""
        # 检查并发和速率限制
        # 这里应该根据具体的并发级别进行检查
        # 暂时简化实现
        
        selected_instance = self.scheduler.select_instance(self.instances)
        
        if selected_instance:
            selected_instance.current_load += 1
        
        return selected_instance
    
    def release_instance(self, instance: LLMInstance) -> None:
        """释放实例"""
        if instance.current_load > 0:
            instance.current_load -= 1
    
    async def call_llm(self, prompt: str, **kwargs) -> Any:
        """调用LLM"""
        instance = await self.get_instance()
        
        if not instance:
            raise LLMError("没有可用的LLM实例")
        
        try:
            start_time = time.time()
            
            # 调用LLM
            # TODO: 实现实际的LLM调用
            result = await self._call_instance(instance, prompt, **kwargs)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 更新统计信息
            self.stats["total_requests"] += 1
            self.stats["successful_requests"] += 1
            self.stats["avg_response_time"] = (
                (self.stats["avg_response_time"] * (self.stats["successful_requests"] - 1) + response_time) / 
                self.stats["successful_requests"]
            )
            
            # 更新实例性能
            instance.update_performance(response_time, True)
            
            return result
            
        except Exception as e:
            self.stats["total_requests"] += 1
            self.stats["failed_requests"] += 1
            
            # 更新实例性能
            instance.update_performance(0, False)
            
            raise e
        finally:
            self.release_instance(instance)
    
    async def _call_instance(self, instance: LLMInstance, prompt: str, **kwargs) -> Any:
        """调用具体实例"""
        # TODO: 实现实际的LLM调用逻辑
        await asyncio.sleep(0.1)  # 模拟调用延迟
        return f"模拟响应: {prompt[:50]}..."
    
    def get_status(self) -> Dict[str, Any]:
        """获取轮询池状态"""
        return {
            "name": self.name,
            "total_instances": len(self.instances),
            "healthy_instances": len([inst for inst in self.instances if inst.status == InstanceStatus.HEALTHY]),
            "degraded_instances": len([inst for inst in self.instances if inst.status == InstanceStatus.DEGRADED]),
            "failed_instances": len([inst for inst in self.instances if inst.status == InstanceStatus.FAILED]),
            "stats": self.stats,
            "concurrency_status": self.concurrency_manager.get_status()
        }
    
    async def shutdown(self) -> None:
        """关闭轮询池"""
        self.health_checker.stop()
        logger.info(f"轮询池 {self.name} 已关闭")


class PollingPoolManager(IPollingPoolManager):
    """轮询池管理器"""
    
    def __init__(self, task_group_manager: TaskGroupManager):
        """
        初始化轮询池管理器
        
        Args:
            task_group_manager: 任务组管理器
        """
        self.task_group_manager = task_group_manager
        self.pools: Dict[str, PollingPool] = {}
    
    async def create_pool(self, name: str, config: Dict[str, Any]) -> PollingPool:
        """创建轮询池"""
        pool = PollingPool(name, config, self.task_group_manager)
        await pool.initialize()
        self.pools[name] = pool
        return pool
    
    def get_pool(self, name: str) -> Optional[PollingPool]:
        """获取轮询池"""
        return self.pools.get(name)
    
    async def shutdown_all(self) -> None:
        """关闭所有轮询池"""
        for pool in self.pools.values():
            await pool.shutdown()
        self.pools.clear()
    
    def get_all_status(self) -> Dict[str, Any]:
        """获取所有轮询池状态"""
        status = {}
        for name, pool in self.pools.items():
            status[name] = pool.get_status()
        return status
    
    def list_all_status(self) -> Dict[str, Any]:
        """获取所有轮询池状态（别名方法，为了兼容接口）"""
        return self.get_all_status()