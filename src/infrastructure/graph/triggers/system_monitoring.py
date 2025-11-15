"""系统监控触发器

提供系统监控功能的触发器实现。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .monitoring_base import MonitoringTrigger, TriggerType
from ..states import WorkflowState


class MemoryMonitoringTrigger(MonitoringTrigger):
    """内存监控触发器
    
    监控内存使用情况，当超过阈值时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化内存监控触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "memory_threshold_mb": 1024,  # 内存阈值（MB）
            "system_memory_threshold_percent": 90,  # 系统内存阈值（百分比）
            "check_interval": 60,  # 检查间隔（秒）
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.CUSTOM, default_config)
        
        self._memory_threshold_mb = self._config["memory_threshold_mb"]
        self._system_memory_threshold_percent = self._config["system_memory_threshold_percent"]
        self._check_interval = self._config["check_interval"]
    
    def evaluate(self, state: WorkflowState, context: Dict[str, Any]) -> bool:
        """评估是否应该触发
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        if not self.can_trigger():
            return False
        
        # 检查内存使用情况
        memory_info = self.check_memory_usage()
        if not memory_info:
            return False
        
        # 检查是否超过阈值
        return (memory_info.process_memory_mb > self._memory_threshold_mb or
                memory_info.system_memory_percent > self._system_memory_threshold_percent)
    
    def execute(self, state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._update_trigger_info()
        
        memory_info = self.check_memory_usage()
        if not memory_info:
            return {
                "error": "无法获取内存信息",
                "executed_at": datetime.now().isoformat()
            }
        
        # 确定警告类型
        warning_types = []
        if memory_info.process_memory_mb > self._memory_threshold_mb:
            warning_types.append("process_memory")
        if memory_info.system_memory_percent > self._system_memory_threshold_percent:
            warning_types.append("system_memory")
        
        return {
            "process_memory_mb": memory_info.process_memory_mb,
            "system_memory_mb": memory_info.system_memory_mb,
            "process_memory_percent": memory_info.process_memory_percent,
            "system_memory_percent": memory_info.system_memory_percent,
            "thresholds": {
                "process_memory_mb": self._memory_threshold_mb,
                "system_memory_percent": self._system_memory_threshold_percent
            },
            "warning_types": warning_types,
            "memory_trend": self._get_memory_trend(),
            "executed_at": datetime.now().isoformat(),
            "message": f"内存使用超过阈值: {', '.join(warning_types)}"
        }
    
    def _get_memory_trend(self) -> Dict[str, Any]:
        """获取内存使用趋势
        
        Returns:
            Dict[str, Any]: 内存趋势信息
        """
        history = self.get_memory_history(10)
        if len(history) < 2:
            return {"trend": "insufficient_data"}
        
        # 计算趋势
        recent = history[-5:] if len(history) >= 5 else history
        process_memory_trend = recent[-1].process_memory_mb - recent[0].process_memory_mb
        system_memory_trend = recent[-1].system_memory_percent - recent[0].system_memory_percent
        
        return {
            "trend": "increasing" if process_memory_trend > 0 else "decreasing",
            "process_memory_change_mb": process_memory_trend,
            "system_memory_change_percent": system_memory_trend,
            "sample_count": len(recent)
        }


class PerformanceMonitoringTrigger(MonitoringTrigger):
    """性能监控触发器
    
    监控系统性能指标，当性能下降时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化性能监控触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "cpu_threshold_percent": 80,  # CPU阈值（百分比）
            "response_time_threshold": 5.0,  # 响应时间阈值（秒）
            "check_interval": 60,  # 检查间隔（秒）
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.CUSTOM, default_config)
        
        self._cpu_threshold_percent = self._config["cpu_threshold_percent"]
        self._response_time_threshold = self._config["response_time_threshold"]
        self._check_interval = self._config["check_interval"]
        self._performance_history: List[Dict[str, Any]] = []
    
    def evaluate(self, state: WorkflowState, context: Dict[str, Any]) -> bool:
        """评估是否应该触发
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        if not self.can_trigger():
            return False
        
        # 收集性能指标
        performance_data = self._collect_performance_data()
        if not performance_data:
            return False
        
        # 检查是否超过阈值
        return (performance_data.get("cpu_percent", 0) > self._cpu_threshold_percent or
                performance_data.get("response_time", 0) > self._response_time_threshold)
    
    def execute(self, state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._update_trigger_info()
        
        performance_data = self._collect_performance_data()
        if not performance_data:
            return {
                "error": "无法获取性能数据",
                "executed_at": datetime.now().isoformat()
            }
        
        # 确定警告类型
        warning_types = []
        if performance_data.get("cpu_percent", 0) > self._cpu_threshold_percent:
            warning_types.append("cpu")
        if performance_data.get("response_time", 0) > self._response_time_threshold:
            warning_types.append("response_time")
        
        return {
            "performance_data": performance_data,
            "thresholds": {
                "cpu_percent": self._cpu_threshold_percent,
                "response_time": self._response_time_threshold
            },
            "warning_types": warning_types,
            "performance_trend": self._get_performance_trend(),
            "executed_at": datetime.now().isoformat(),
            "message": f"性能指标超过阈值: {', '.join(warning_types)}"
        }
    
    def _collect_performance_data(self) -> Optional[Dict[str, Any]]:
        """收集性能数据
        
        Returns:
            Optional[Dict[str, Any]]: 性能数据
        """
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 响应时间（从状态中获取）
            response_time = 0
            messages = self._state_info.state_data.get("messages", [])
            if messages:
                latest_message = messages[-1]
                response_time = latest_message.get("response_time", 0)
            
            performance_data = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "response_time": response_time,
                "process_count": len(psutil.pids()),
                "boot_time": psutil.boot_time()
            }
            
            # 添加到历史记录
            self._performance_history.append(performance_data)
            if len(self._performance_history) > self._max_history_size:
                self._performance_history = self._performance_history[-self._max_history_size:]
            
            return performance_data
            
        except Exception:
            return None
    
    def _get_performance_trend(self) -> Dict[str, Any]:
        """获取性能趋势
        
        Returns:
            Dict[str, Any]: 性能趋势信息
        """
        if len(self._performance_history) < 2:
            return {"trend": "insufficient_data"}
        
        # 计算趋势
        recent = self._performance_history[-5:] if len(self._performance_history) >= 5 else self._performance_history
        cpu_trend = recent[-1]["cpu_percent"] - recent[0]["cpu_percent"]
        response_time_trend = recent[-1]["response_time"] - recent[0]["response_time"]
        
        return {
            "trend": "degrading" if cpu_trend > 0 or response_time_trend > 0 else "improving",
            "cpu_change_percent": cpu_trend,
            "response_time_change": response_time_trend,
            "sample_count": len(recent)
        }


class ResourceMonitoringTrigger(MonitoringTrigger):
    """资源监控触发器
    
    监控系统资源使用情况，当资源不足时触发。
    """
    
    def __init__(
        self,
        trigger_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化资源监控触发器
        
        Args:
            trigger_id: 触发器ID
            config: 触发器配置
        """
        default_config = {
            "disk_threshold_percent": 90,  # 磁盘空间阈值（百分比）
            "memory_threshold_percent": 90,  # 内存阈值（百分比）
            "check_interval": 300,  # 检查间隔（秒）
            "max_history_size": 100
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(trigger_id, TriggerType.CUSTOM, default_config)
        
        self._disk_threshold_percent = self._config["disk_threshold_percent"]
        self._memory_threshold_percent = self._config["memory_threshold_percent"]
        self._check_interval = self._config["check_interval"]
        self._resource_history: List[Dict[str, Any]] = []
    
    def evaluate(self, state: WorkflowState, context: Dict[str, Any]) -> bool:
        """评估是否应该触发
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该触发
        """
        if not self.can_trigger():
            return False
        
        # 收集资源数据
        resource_data = self._collect_resource_data()
        if not resource_data:
            return False
        
        # 检查是否超过阈值
        return (resource_data.get("disk_percent", 0) > self._disk_threshold_percent or
                resource_data.get("memory_percent", 0) > self._memory_threshold_percent)
    
    def execute(self, state: WorkflowState, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行触发器动作
        
        Args:
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._update_trigger_info()
        
        resource_data = self._collect_resource_data()
        if not resource_data:
            return {
                "error": "无法获取资源数据",
                "executed_at": datetime.now().isoformat()
            }
        
        # 确定警告类型
        warning_types = []
        if resource_data.get("disk_percent", 0) > self._disk_threshold_percent:
            warning_types.append("disk")
        if resource_data.get("memory_percent", 0) > self._memory_threshold_percent:
            warning_types.append("memory")
        
        return {
            "resource_data": resource_data,
            "thresholds": {
                "disk_percent": self._disk_threshold_percent,
                "memory_percent": self._memory_threshold_percent
            },
            "warning_types": warning_types,
            "resource_trend": self._get_resource_trend(),
            "executed_at": datetime.now().isoformat(),
            "message": f"系统资源不足: {', '.join(warning_types)}"
        }
    
    def _collect_resource_data(self) -> Optional[Dict[str, Any]]:
        """收集资源数据
        
        Returns:
            Optional[Dict[str, Any]]: 资源数据
        """
        try:
            import psutil
            
            # 磁盘使用情况
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            resource_data = {
                "timestamp": datetime.now().isoformat(),
                "disk_percent": disk_percent,
                "disk_free_gb": disk_usage.free / (1024**3),
                "disk_total_gb": disk_usage.total / (1024**3),
                "memory_percent": memory_percent,
                "memory_free_gb": memory.available / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
            # 添加到历史记录
            self._resource_history.append(resource_data)
            if len(self._resource_history) > self._max_history_size:
                self._resource_history = self._resource_history[-self._max_history_size:]
            
            return resource_data
            
        except Exception:
            return None
    
    def _get_resource_trend(self) -> Dict[str, Any]:
        """获取资源趋势
        
        Returns:
            Dict[str, Any]: 资源趋势信息
        """
        if len(self._resource_history) < 2:
            return {"trend": "insufficient_data"}
        
        # 计算趋势
        recent = self._resource_history[-5:] if len(self._resource_history) >= 5 else self._resource_history
        disk_trend = recent[-1]["disk_percent"] - recent[0]["disk_percent"]
        memory_trend = recent[-1]["memory_percent"] - recent[0]["memory_percent"]
        
        return {
            "trend": "increasing" if disk_trend > 0 or memory_trend > 0 else "stable",
            "disk_change_percent": disk_trend,
            "memory_change_percent": memory_trend,
            "sample_count": len(recent)
        }