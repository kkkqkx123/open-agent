现在我来设计基于配置的迭代管理系统：

## 基于配置的迭代管理系统详细设计

### 1. 迭代管理器配置

```yaml
# configs/iteration_managers.yaml
metadata:
  name: "iteration_managers_config"
  version: "1.0.0"
  description: "迭代管理器配置"
  author: "system"

# 迭代管理器定义
iteration_managers:
  simple:
    description: "简单迭代管理器"
    class_path: "src.core.workflow.iteration.simple_manager:SimpleIterationManager"
    enabled: true
    priority: 100
    tags: ["simple", "basic", "lightweight"]
    default_config:
      max_iterations: 100
      enable_tracking: true
      enable_metrics: false
      enable_persistence: false
      cleanup_on_complete: true
    parameters:
      # 全局限制
      global_max_iterations: 1000
      per_node_max_iterations: 100
      
      # 跟踪配置
      track_execution_time: true
      track_memory_usage: false
      track_node_performance: false
      
      # 持久化配置
      persistence_enabled: false
      persistence_backend: "memory"
      persistence_interval: 10
      
      # 清理配置
      auto_cleanup: true
      cleanup_threshold: 1000
      retain_completed_records: 100
      
    metadata:
      author: "system"
      version: "1.0.0"
      category: "basic_iteration"
      
  advanced:
    description: "高级迭代管理器"
    class_path: "src.core.workflow.iteration.advanced_manager:AdvancedIterationManager"
    enabled: true
    priority: 90
    tags: ["advanced", "feature-rich", "production"]
    default_config:
      max_iterations: 1000
      enable_tracking: true
      enable_metrics: true
      enable_persistence: true
      cleanup_on_complete: false
    parameters:
      # 全局限制
      global_max_iterations: 10000
      per_node_max_iterations: 1000
      per_workflow_max_iterations: 5000
      
      # 跟踪配置
      track_execution_time: true
      track_memory_usage: true
      track_node_performance: true
      track_resource_usage: true
      track_error_patterns: true
      
      # 持久化配置
      persistence_enabled: true
      persistence_backend: "sqlite"
      persistence_interval: 1
      persistence_config:
        database_path: "${ITERATION_DB_PATH:data/iterations.db}"
        connection_pool_size: 5
        connection_timeout: 30
        
      # 清理配置
      auto_cleanup: true
      cleanup_threshold: 10000
      retain_completed_records: 1000
      retain_failed_records: 500
      
      # 高级功能
      enable_adaptive_limits: true
      enable_predictive_analysis: false
      enable_real_time_monitoring: true
      enable_alerts: true
      
      # 告警配置
      alert_thresholds:
        iteration_count_warning: 80
        iteration_count_critical: 95
        execution_time_warning: 300  # 5分钟
        execution_time_critical: 600  # 10分钟
        memory_usage_warning: 0.8  # 80%
        memory_usage_critical: 0.9  # 90%
        
    metadata:
      author: "system"
      version: "1.0.0"
      category: "advanced_iteration"
      
  distributed:
    description: "分布式迭代管理器"
    class_path: "src.core.workflow.iteration.distributed_manager:DistributedIterationManager"
    enabled: false
    priority: 80
    tags: ["distributed", "cluster", "scalable"]
    default_config:
      max_iterations: 10000
      enable_tracking: true
      enable_metrics: true
      enable_persistence: true
      cleanup_on_complete: false
    parameters:
      # 分布式配置
      cluster_enabled: true
      cluster_nodes: ["node1", "node2", "node3"]
      coordination_backend: "redis"
      coordination_config:
        host: "${REDIS_HOST:localhost}"
        port: "${REDIS_PORT:6379}"
        db: 0
        password: "${REDIS_PASSWORD:}"
        
      # 全局限制
      global_max_iterations: 100000
      per_node_max_iterations: 10000
      per_workflow_max_iterations: 50000
      
      # 跟踪配置
      track_execution_time: true
      track_memory_usage: true
      track_node_performance: true
      track_resource_usage: true
      track_network_usage: true
      track_error_patterns: true
      
      # 持久化配置
      persistence_enabled: true
      persistence_backend: "distributed"
      persistence_interval: 1
      persistence_config:
        replication_factor: 3
        consistency_level: "quorum"
        
      # 清理配置
      auto_cleanup: true
      cleanup_threshold: 100000
      retain_completed_records: 10000
      retain_failed_records: 5000
      
      # 分布式功能
      enable_load_balancing: true
      enable_failover: true
      enable_consistency_checks: true
      enable_distributed_locks: true
      
    metadata:
      author: "system"
      version: "1.0.0"
      category: "distributed_iteration"

# 默认管理器
default_manager: "simple"

# 管理器组定义
manager_groups:
  basic:
    description: "基础管理器组"
    managers:
      - "simple"
      
  production:
    description: "生产环境管理器组"
    managers:
      - "advanced"
      
  enterprise:
    description: "企业级管理器组"
    managers:
      - "advanced"
      - "distributed"

# 全局配置
global_config:
  # 默认限制
  default_max_iterations: 100
  default_timeout: 300  # 5分钟
  
  # 监控配置
  monitoring_enabled: true
  monitoring_interval: 10  # 10秒
  
  # 日志配置
  logging_enabled: true
  log_level: "INFO"
  log_format: "structured"
  
  # 性能配置
  cache_enabled: true
  cache_size: 10000
  cache_ttl: 3600  # 1小时

# 验证规则
validation_rules:
  - field: "iteration_managers.*.class_path"
    rule_type: "required"
    message: "迭代管理器必须指定类路径"
  - field: "iteration_managers.*.parameters.global_max_iterations"
    rule_type: "range"
    value: [1, 1000000]
    message: "全局最大迭代次数必须在1-1000000之间"
  - field: "iteration_managers.*.parameters.per_node_max_iterations"
    rule_type: "range"
    value: [1, 100000]
    message: "每节点最大迭代次数必须在1-100000之间"
```

### 2. 迭代管理器接口设计

```python
# src/core/workflow/iteration/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

class IterationStatus(Enum):
    """迭代状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class IterationRecord:
    """迭代记录"""
    
    def __init__(
        self,
        node_name: str,
        iteration_count: int,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        status: IterationStatus = IterationStatus.PENDING,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.node_name = node_name
        self.iteration_count = iteration_count
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        self.error = error
        self.metadata = metadata or {}
        self.duration = (end_time - start_time).total_seconds() if end_time else None

class IIterationManager(ABC):
    """迭代管理器接口"""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化迭代管理器"""
        pass
    
    @abstractmethod
    def check_limits(self, state: Any, node_name: str) -> bool:
        """检查迭代限制"""
        pass
    
    @abstractmethod
    def record_iteration(
        self,
        state: Dict[str, Any],
        node_name: str,
        start_time: datetime,
        end_time: datetime,
        status: str = 'SUCCESS',
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """记录迭代"""
        pass
    
    @abstractmethod
    def get_iteration_count(self, node_name: str) -> int:
        """获取迭代次数"""
        pass
    
    @abstractmethod
    def get_iteration_records(self, node_name: Optional[str] = None) -> List[IterationRecord]:
        """获取迭代记录"""
        pass
    
    @abstractmethod
    def reset_iterations(self, node_name: Optional[str] = None) -> None:
        """重置迭代计数"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
```

### 3. 简单迭代管理器实现

```python
# src/core/workflow/iteration/simple_manager.py
class SimpleIterationManager(IIterationManager):
    """简单迭代管理器实现"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.iteration_counts: Dict[str, int] = {}
        self.iteration_records: List[IterationRecord] = []
        self._initialized = False
        
    def initialize(self, config: Dict[str, Any]) -> None:
        """初始化迭代管理器"""
        self.config.update(config)
        self._initialized = True
        
        # 设置默认值
        self.max_iterations = self.config.get("max_iterations", 100)
        self.global_max_iterations = self.config.get("global_max_iterations", 1000)
        self.per_node_max_iterations = self.config.get("per_node_max_iterations", 100)
        self.enable_tracking = self.config.get("enable_tracking", True)
        self.cleanup_on_complete = self.config.get("cleanup_on_complete", True)
        
    def check_limits(self, state: Any, node_name: str) -> bool:
        """检查迭代限制"""
        if not self._initialized:
            return True
            
        current_count = self.iteration_counts.get(node_name, 0)
        
        # 检查节点级别限制
        if current_count >= self.per_node_max_iterations:
            return False
            
        # 检查全局限制
        total_iterations = sum(self.iteration_counts.values())
        if total_iterations >= self.global_max_iterations:
            return False
            
        return True
    
    def record_iteration(
        self,
        state: Dict[str, Any],
        node_name: str,
        start_time: datetime,
        end_time: datetime,
        status: str = 'SUCCESS',
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """记录迭代"""
        if not self._initialized:
            return state
            
        # 增加迭代计数
        self.iteration_counts[node_name] = self.iteration_counts.get(node_name, 0) + 1
        
        # 创建迭代记录
        if self.enable_tracking:
            iteration_status = IterationStatus(status.upper())
            record = IterationRecord(
                node_name=node_name,
                iteration_count=self.iteration_counts[node_name],
                start_time=start_time,
                end_time=end_time,
                status=iteration_status,
                error=error,
                metadata=metadata
            )
            self.iteration_records.append(record)
        
        # 更新状态
        updated_state = dict(state)
        updated_state['iteration_count'] = self.iteration_counts[node_name]
        updated_state['total_iterations'] = sum(self.iteration_counts.values())
        
        return updated_state
    
    def get_iteration_count(self, node_name: str) -> int:
        """获取迭代次数"""
        return self.iteration_counts.get(node_name, 0)
    
    def get_iteration_records(self, node_name: Optional[str] = None) -> List[IterationRecord]:
        """获取迭代记录"""
        if node_name:
            return [record for record in self.iteration_records if record.node_name == node_name]
        return self.iteration_records.copy()
    
    def reset_iterations(self, node_name: Optional[str] = None) -> None:
        """重置迭代计数"""
        if node_name:
            self.iteration_counts.pop(node_name, None)
            self.iteration_records = [record for record in self.iteration_records if record.node_name != node_name]
        else:
            self.iteration_counts.clear()
            self.iteration_records.clear()
    
    def cleanup(self) -> None:
        """清理资源"""
        if self.cleanup_on_complete:
            # 保留最近的记录
            if len(self.iteration_records) > 1000:
                self.iteration_records = self.iteration_records[-1000:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_iterations = sum(self.iteration_counts.values())
        successful_iterations = len([r for r in self.iteration_records if r.status == IterationStatus.COMPLETED])
        failed_iterations = len([r for r in self.iteration_records if r.status == IterationStatus.FAILED])
        
        return {
            "total_iterations": total_iterations,
            "node_counts": self.iteration_counts.copy(),
            "total_records": len(self.iteration_records),
            "successful_iterations": successful_iterations,
            "failed_iterations": failed_iterations,
            "success_rate": successful_iterations / len(self.iteration_records) if self.iteration_records else 0,
            "average_duration": sum(r.duration for r in self.iteration_records if r.duration) / len(self.iteration_records) if self.iteration_records else 0
        }
```

### 4. 迭代管理器工厂

```python
# src/core/workflow/iteration/manager_factory.py
class IterationManagerFactory:
    """迭代管理器工厂"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._manager_cache: Dict[str, IIterationManager] = {}
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        
    def create_manager(self, manager_type: str, **kwargs) -> IIterationManager:
        """创建迭代管理器"""
        # 检查缓存
        if manager_type in self._manager_cache:
            return self._manager_cache[manager_type]
        
        # 获取管理器配置
        manager_config = self._get_manager_config(manager_type)
        if not manager_config:
            raise ValueError(f"未找到迭代管理器配置: {manager_type}")
        
        # 检查是否启用
        if not manager_config.get("enabled", True):
            raise ValueError(f"迭代管理器未启用: {manager_type}")
        
        try:
            # 动态导入类
            class_path = manager_config["class_path"]
            manager_class = self._import_class(class_path)
            
            # 合并配置
            config = {
                **manager_config.get("default_config", {}),
                **manager_config.get("parameters", {}),
                **kwargs
            }
            
            # 创建管理器实例
            if hasattr(manager_class, "create"):
                # 工厂方法
                manager = manager_class.create(config)
            else:
                # 直接实例化
                manager = manager_class(config)
            
            # 初始化管理器
            manager.initialize(config)
            
            # 缓存管理器
            self._manager_cache[manager_type] = manager
            
            return manager
            
        except Exception as e:
            logger.error(f"创建迭代管理器失败 {manager_type}: {e}")
            raise
    
    def _get_manager_config(self, manager_type: str) -> Optional[Dict[str, Any]]:
        """获取管理器配置"""
        if manager_type in self._config_cache:
            return self._config_cache[manager_type]
        
        # 加载配置文件
        config_file = "configs/iteration_managers.yaml"
        try:
            config_data = self.config_manager.load_config(config_file)
            managers = config_data.get("iteration_managers", {})
            manager_config = managers.get(manager_type)
            
            if manager_config:
                self._config_cache[manager_type] = manager_config
                return manager_config
        except Exception as e:
            logger.error(f"加载迭代管理器配置失败 {manager_type}: {e}")
        
        return None
    
    def _import_class(self, class_path: str) -> type:
        """动态导入类"""
        module_path, class_name = class_path.rsplit(":", 1)
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    
    def get_default_manager(self) -> IIterationManager:
        """获取默认管理器"""
        config_file = "configs/iteration_managers.yaml"
        try:
            config_data = self.config_manager.load_config(config_file)
            default_type = config_data.get("default_manager", "simple")
            return self.create_manager(default_type)
        except Exception as e:
            logger.error(f"获取默认迭代管理器失败: {e}")
            # 回退到简单管理器
            return self.create_manager("simple")
    
    def list_available_managers(self) -> List[str]:
        """列出可用的管理器"""
        config_file = "configs/iteration_managers.yaml"
        try:
            config_data = self.config_manager.load_config(config_file)
            managers = config_data.get("iteration_managers", {})
            return [name for name, config in managers.items() if config.get("enabled", True)]
        except Exception as e:
            logger.error(f"列出可用迭代管理器失败: {e}")
            return ["simple"]  # 回退到简单管理器
```

这个设计提供了：

1. **多种管理器类型**：简单、高级、分布式迭代管理器
2. **完全配置驱动**：所有管理器都通过配置文件定义
3. **动态加载**：运行时根据配置动态创建管理器
4. **缓存优化**：支持管理器实例缓存
5. **丰富的功能**：跟踪、持久化、监控、告警等
6. **扩展性**：易于添加新的管理器类型
7. **向后兼容**：保持现有API不变