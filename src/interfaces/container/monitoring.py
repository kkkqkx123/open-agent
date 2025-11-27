"""
监控和分析接口

定义服务跟踪、性能监控和依赖分析的相关接口。
"""

from abc import ABC, abstractmethod
from typing import Type, Dict, Any, Optional, List, Set
from dataclasses import dataclass
from datetime import datetime

from .core import DependencyChain


'''
服务跟踪接口
'''

class IServiceTracker(ABC):
    """
    服务跟踪接口
    
    负责跟踪服务的创建和释放，提供服务实例的生命周期监控。
    这是容器监控的基础组件，用于了解服务的使用情况。
    
    主要功能：
    - 服务创建跟踪
    - 服务释放跟踪
    - 实例计数统计
    - 生命周期监控
    
    使用示例：
        ```python
        # 跟踪服务创建
        tracker.track_creation(IUserService, user_instance)
        
        # 跟踪服务释放
        tracker.track_disposal(IUserService, user_instance)
        
        # 获取跟踪信息
        tracked_services = tracker.get_tracked_services()
        ```
    """
    
    @abstractmethod
    def track_creation(self, service_type: Type, instance: Any) -> None:
        """
        跟踪服务创建
        
        记录服务实例的创建信息，包括创建时间、实例ID等。
        
        Args:
            service_type: 服务类型
            instance: 服务实例
            
        Examples:
            ```python
            # 在服务创建时调用
            instance = UserService()
            tracker.track_creation(IUserService, instance)
            
            # 自动跟踪（通过容器）
            container.register(IUserService, UserService)
            # 容器内部会自动调用 track_creation
            ```
        """
        pass
    
    @abstractmethod
    def track_disposal(self, service_type: Type, instance: Any) -> None:
        """
        跟踪服务释放
        
        记录服务实例的释放信息，包括释放时间、生命周期等。
        
        Args:
            service_type: 服务类型
            instance: 服务实例
            
        Examples:
            ```python
            # 在服务释放时调用
            instance.dispose()
            tracker.track_disposal(IUserService, instance)
            
            # 自动跟踪（通过容器）
            container.clear()
            # 容器内部会自动调用 track_disposal
            ```
        """
        pass
    
    @abstractmethod
    def get_tracked_services(self) -> Dict[Type, List[Any]]:
        """
        获取跟踪的服务
        
        返回所有被跟踪的服务类型及其实例列表。
        
        Returns:
            Dict[Type, List[Any]]: 服务类型到实例列表的映射
            
        Examples:
            ```python
            tracked = tracker.get_tracked_services()
            for service_type, instances in tracked.items():
                print(f"{service_type.__name__}: {len(instances)} instances")
                
                for instance in instances:
                    print(f"  - {id(instance)}")
            ```
        """
        pass
    
    @abstractmethod
    def get_instance_count(self, service_type: Type) -> int:
        """
        获取服务实例数量
        
        Args:
            service_type: 服务类型
            
        Returns:
            int: 实例数量
            
        Examples:
            ```python
            count = tracker.get_instance_count(IUserService)
            print(f"UserService instances: {count}")
            
            # 监控实例数量
            if count > 1:
                logger.warning(f"Multiple instances of {IUserService.__name__} detected")
            ```
        """
        pass
    
    @abstractmethod
    def get_instance_info(self, service_type: Type, instance: Any) -> Optional[Dict[str, Any]]:
        """
        获取实例信息
        
        Args:
            service_type: 服务类型
            instance: 服务实例
            
        Returns:
            Optional[Dict[str, Any]]: 实例信息，如果未跟踪则返回None
            
        Examples:
            ```python
            info = tracker.get_instance_info(IUserService, instance)
            if info:
                print(f"Created at: {info['created_at']}")
                print(f"Lifetime: {info['lifetime']} seconds")
                print(f"Access count: {info['access_count']}")
            ```
        """
        pass
    
    @abstractmethod
    def get_total_instance_count(self) -> int:
        """
        获取总实例数量
        
        Returns:
            int: 所有服务的实例总数
            
        Examples:
            ```python
            total = tracker.get_total_instance_count()
            print(f"Total tracked instances: {total}")
            
            # 内存监控
            if total > 1000:
                logger.warning("High instance count detected")
            ```
        """
        pass
    
    @abstractmethod
    def clear_tracking(self, service_type: Optional[Type] = None) -> int:
        """
        清除跟踪信息
        
        Args:
            service_type: 要清除的服务类型，None表示清除所有
            
        Returns:
            int: 清除的跟踪条目数量
            
        Examples:
            ```python
            # 清除特定服务的跟踪
            cleared = tracker.clear_tracking(IUserService)
            
            # 清除所有跟踪
            total_cleared = tracker.clear_tracking()
            print(f"Cleared {total_cleared} tracking entries")
            ```
        """
        pass


'''
性能监控接口
'''

@dataclass
class PerformanceMetrics:
    """
    性能指标数据类
    
    封装性能相关的指标数据。
    """
    service_type: Type
    operation_type: str
    duration: float
    timestamp: datetime
    success: bool
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class IPerformanceMonitor(ABC):
    """
    性能监控接口
    
    负责监控容器操作的性能指标，包括解析时间、缓存命中率等。
    提供性能分析和优化建议。
    
    主要功能：
    - 操作时间记录
    - 缓存命中率统计
    - 性能指标分析
    - 性能报告生成
    
    使用示例：
        ```python
        # 记录性能指标
        monitor.record_resolution(IUserService, start_time, end_time)
        
        # 获取统计信息
        stats = monitor.get_stats()
        
        # 生成性能报告
        report = monitor.generate_report()
        ```
    """
    
    @abstractmethod
    def record_resolution(self, service_type: Type, start_time: float, end_time: float) -> None:
        """
        记录服务解析性能
        
        Args:
            service_type: 服务类型
            start_time: 开始时间（时间戳）
            end_time: 结束时间（时间戳）
            
        Examples:
            ```python
            # 手动记录
            start = time.time()
            instance = container.get(IUserService)
            end = time.time()
            monitor.record_resolution(IUserService, start, end)
            
            # 自动记录（通过容器）
            # 容器内部会自动调用 record_resolution
            ```
        """
        pass
    
    @abstractmethod
    def record_cache_hit(self, service_type: Type) -> None:
        """
        记录缓存命中
        
        Args:
            service_type: 服务类型
            
        Examples:
            ```python
            # 在缓存命中时调用
            if cache.contains(service_type):
                monitor.record_cache_hit(service_type)
                return cache.get(service_type)
            ```
        """
        pass
    
    @abstractmethod
    def record_cache_miss(self, service_type: Type) -> None:
        """
        记录缓存未命中
        
        Args:
            service_type: 服务类型
            
        Examples:
            ```python
            # 在缓存未命中时调用
            if not cache.contains(service_type):
                monitor.record_cache_miss(service_type)
                instance = create_service(service_type)
                cache.put(service_type, instance)
                return instance
            ```
        """
        pass
    
    @abstractmethod
    def record_operation(self, metrics: PerformanceMetrics) -> None:
        """
        记录操作指标
        
        Args:
            metrics: 性能指标数据
            
        Examples:
            ```python
            # 记录自定义操作
            metrics = PerformanceMetrics(
                service_type=IUserService,
                operation_type="database_query",
                duration=0.05,
                timestamp=datetime.now(),
                success=True,
                metadata={"query": "SELECT * FROM users"}
            )
            monitor.record_operation(metrics)
            ```
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            Dict[str, Any]: 性能统计信息
            
        Examples:
            ```python
            stats = monitor.get_stats()
            print(f"Average resolution time: {stats['avg_resolution_time']:.3f}s")
            print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
            print(f"Total operations: {stats['total_operations']}")
            print(f"Success rate: {stats['success_rate']:.2%}")
            ```
        """
        pass
    
    @abstractmethod
    def get_service_stats(self, service_type: Type) -> Dict[str, Any]:
        """
        获取特定服务的性能统计
        
        Args:
            service_type: 服务类型
            
        Returns:
            Dict[str, Any]: 服务性能统计信息
            
        Examples:
            ```python
            stats = monitor.get_service_stats(IUserService)
            print(f"UserService stats:")
            print(f"  Average time: {stats['avg_time']:.3f}s")
            print(f"  Call count: {stats['call_count']}")
            print(f"  Success rate: {stats['success_rate']:.2%}")
            ```
        """
        pass
    
    @abstractmethod
    def get_slow_operations(self, threshold: float = 1.0) -> List[PerformanceMetrics]:
        """
        获取慢操作列表
        
        Args:
            threshold: 时间阈值（秒）
            
        Returns:
            List[PerformanceMetrics]: 慢操作指标列表
            
        Examples:
            ```python
            # 获取超过1秒的操作
            slow_ops = monitor.get_slow_operations(1.0)
            for op in slow_ops:
                print(f"Slow operation: {op.service_type.__name__} took {op.duration:.3f}s")
            
            # 分析性能瓶颈
            if slow_ops:
                logger.warning(f"Found {len(slow_ops)} slow operations")
            ```
        """
        pass
    
    @abstractmethod
    def generate_report(self, time_range: Optional[tuple] = None) -> Dict[str, Any]:
        """
        生成性能报告
        
        Args:
            time_range: 时间范围（开始时间，结束时间），None表示全部
            
        Returns:
            Dict[str, Any]: 性能报告
            
        Examples:
            ```python
            # 生成完整报告
            report = monitor.generate_report()
            
            # 生成指定时间范围的报告
            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now()
            report = monitor.generate_report((start_time, end_time))
            
            # 分析报告
            print(f"Performance Report:")
            print(f"  Total operations: {report['total_operations']}")
            print(f"  Average time: {report['avg_time']:.3f}s")
            print(f"  P95 time: {report['p95_time']:.3f}s")
            print(f"  Cache hit rate: {report['cache_hit_rate']:.2%}")
            ```
        """
        pass
    
    @abstractmethod
    def clear_metrics(self, service_type: Optional[Type] = None) -> int:
        """
        清除性能指标
        
        Args:
            service_type: 要清除的服务类型，None表示清除所有
            
        Returns:
            int: 清除的指标数量
            
        Examples:
            ```python
            # 清除特定服务的指标
            cleared = monitor.clear_metrics(IUserService)
            
            # 清除所有指标
            total_cleared = monitor.clear_metrics()
            print(f"Cleared {total_cleared} metrics")
            ```
        """
        pass


'''
依赖分析接口
'''

class IDependencyAnalyzer(ABC):
    """
    依赖分析接口
    
    负责分析服务之间的依赖关系，检测循环依赖和计算依赖深度。
    提供依赖关系可视化和优化建议。
    
    主要功能：
    - 依赖关系构建
    - 循环依赖检测
    - 依赖深度计算
    - 依赖关系分析
    
    使用示例：
        ```python
        # 添加依赖关系
        analyzer.add_dependency(IUserService, IRepository)
        
        # 检测循环依赖
        circular_deps = analyzer.detect_circular_dependencies()
        
        # 计算依赖深度
        depth = analyzer.calculate_dependency_depth(IUserService)
        ```
    """
    
    @abstractmethod
    def add_dependency(self, service_type: Type, dependency_type: Type) -> None:
        """
        添加依赖关系
        
        Args:
            service_type: 服务类型
            dependency_type: 依赖类型
            
        Examples:
            ```python
            # 手动添加依赖关系
            analyzer.add_dependency(IUserService, IRepository)
            analyzer.add_dependency(IUserService, ILogger)
            analyzer.add_dependency(IOrderService, IUserService)
            
            # 自动分析（通过容器）
            # 容器注册时会自动调用 add_dependency
            ```
        """
        pass
    
    @abstractmethod
    def remove_dependency(self, service_type: Type, dependency_type: Type) -> bool:
        """
        移除依赖关系
        
        Args:
            service_type: 服务类型
            dependency_type: 依赖类型
            
        Returns:
            bool: 是否成功移除
            
        Examples:
            ```python
            # 移除依赖关系
            success = analyzer.remove_dependency(IUserService, IRepository)
            if success:
                print("Dependency removed successfully")
            ```
        """
        pass
    
    @abstractmethod
    def get_dependencies(self, service_type: Type) -> Set[Type]:
        """
        获取服务的依赖
        
        Args:
            service_type: 服务类型
            
        Returns:
            Set[Type]: 依赖类型集合
            
        Examples:
            ```python
            deps = analyzer.get_dependencies(IUserService)
            print(f"UserService dependencies:")
            for dep in deps:
                print(f"  - {dep.__name__}")
            ```
        """
        pass
    
    @abstractmethod
    def get_dependents(self, service_type: Type) -> Set[Type]:
        """
        获取依赖指定服务的服务列表
        
        Args:
            service_type: 服务类型
            
        Returns:
            Set[Type]: 依赖该服务的类型集合
            
        Examples:
            ```python
            dependents = analyzer.get_dependents(IRepository)
            print(f"Services depending on Repository:")
            for dependent in dependents:
                print(f"  - {dependent.__name__}")
            ```
        """
        pass
    
    @abstractmethod
    def detect_circular_dependencies(self) -> List[DependencyChain]:
        """
        检测循环依赖
        
        Returns:
            List[DependencyChain]: 循环依赖链列表
            
        Examples:
            ```python
            circular_deps = analyzer.detect_circular_dependencies()
            if circular_deps:
                print(f"Found {len(circular_deps)} circular dependencies:")
                for chain in circular_deps:
                    path = " -> ".join([t.__name__ for t in chain.dependencies])
                    print(f"  {chain.service_type.__name__}: {path}")
            else:
                print("No circular dependencies detected")
            ```
        """
        pass
    
    @abstractmethod
    def calculate_dependency_depth(self, service_type: Type) -> int:
        """
        计算依赖深度
        
        Args:
            service_type: 服务类型
            
        Returns:
            int: 依赖深度
            
        Examples:
            ```python
            depth = analyzer.calculate_dependency_depth(IUserService)
            print(f"UserService dependency depth: {depth}")
            
            # 监控依赖深度
            if depth > 5:
                logger.warning(f"Deep dependency chain detected: {depth}")
            ```
        """
        pass
    
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        分析依赖关系
        
        Returns:
            Dict[str, Any]: 分析结果
            
        Examples:
            ```python
            analysis = analyzer.analyze()
            print(f"Dependency Analysis:")
            print(f"  Total services: {analysis['total_services']}")
            print(f"  Total dependencies: {analysis['total_dependencies']}")
            print(f"  Average depth: {analysis['avg_depth']:.2f}")
            print(f"  Max depth: {analysis['max_depth']}")
            print(f"  Circular dependencies: {analysis['circular_dependencies']}")
            ```
        """
        pass
    
    @abstractmethod
    def update_from_implementation(self, interface: Type, implementation: Type) -> None:
        """
        从实现类更新依赖关系
        
        通过分析实现类的构造函数参数，自动推断依赖关系。
        
        Args:
            interface: 接口类型
            implementation: 实现类型
            
        Examples:
            ```python
            # 自动分析依赖
            analyzer.update_from_implementation(IUserService, UserService)
            
            # 批量分析
            for interface, impl in service_implementations.items():
                analyzer.update_from_implementation(interface, impl)
            ```
        """
        pass
    
    @abstractmethod
    def get_dependency_graph(self) -> Dict[Type, Set[Type]]:
        """
        获取依赖关系图
        
        Returns:
            Dict[Type, Set[Type]]: 服务类型到依赖集合的映射
            
        Examples:
            ```python
            graph = analyzer.get_dependency_graph()
            
            # 可视化依赖关系
            for service, deps in graph.items():
                print(f"{service.__name__} depends on:")
                for dep in deps:
                    print(f"  - {dep.__name__}")
            ```
        """
        pass
    
    @abstractmethod
    def find_leaf_services(self) -> List[Type]:
        """
        查找叶子服务（没有依赖的服务）
        
        Returns:
            List[Type]: 叶子服务类型列表
            
        Examples:
            ```python
            leaf_services = analyzer.find_leaf_services()
            print(f"Leaf services: {[s.__name__ for s in leaf_services]}")
            
            # 优先初始化叶子服务
            for service in leaf_services:
                container.get(service)
            ```
        """
        pass
    
    @abstractmethod
    def find_root_services(self) -> List[Type]:
        """
        查找根服务（没有被依赖的服务）
        
        Returns:
            List[Type]: 根服务类型列表
            
        Examples:
            ```python
            root_services = analyzer.find_root_services()
            print(f"Root services: {[s.__name__ for s in root_services]}")
            
            # 最后释放根服务
            for service in reversed(root_services):
                container.dispose(service)
            ```
        """
        pass