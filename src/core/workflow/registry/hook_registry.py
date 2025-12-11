"""Hook注册表

管理Hook的注册、获取和执行。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from src.interfaces.workflow.hooks import IHook, IHookRegistry, HookPoint
from src.interfaces.dependency_injection import get_logger
from .base_registry import BaseRegistry

logger = get_logger(__name__)


@dataclass
class HookRegistration:
    """Hook注册信息"""
    hook: IHook
    priority: int
    registered_at: str


class HookRegistry(BaseRegistry, IHookRegistry):
    """Hook注册表实现
    
    管理所有Hook的注册、注销和获取。
    """
    
    def __init__(self):
        """初始化Hook注册表"""
        super().__init__("hook")
        self._hooks: Dict[HookPoint, List[HookRegistration]] = {}
        self._hook_dict: Dict[str, IHook] = {}  # 通过hook_id快速查找
    
    def register_hook(
        self,
        hook_point: HookPoint,
        hook: IHook,
        priority: int = 50
    ) -> None:
        """注册Hook
        
        Args:
            hook_point: Hook点
            hook: Hook实例
            priority: 优先级，数值越小优先级越高
        """
        if hook_point not in self._hooks:
            self._hooks[hook_point] = []
        
        # 检查是否已注册
        for registration in self._hooks[hook_point]:
            if registration.hook.hook_id == hook.hook_id:
                self._logger.warning(f"Hook {hook.hook_id} 已在 {hook_point.value} 点注册，将被覆盖")
                self._hooks[hook_point].remove(registration)
                if hook.hook_id in self._hook_dict:
                    del self._hook_dict[hook.hook_id]
        
        from datetime import datetime
        registration = HookRegistration(
            hook=hook,
            priority=priority,
            registered_at=datetime.now().isoformat()
        )
        self._hooks[hook_point].append(registration)
        self._hook_dict[hook.hook_id] = hook
        
        # 按优先级排序
        self._hooks[hook_point].sort(key=lambda r: r.priority)
        
        self._logger.debug(f"Hook {hook.hook_id} 已注册到 {hook_point.value} 点，优先级: {priority}")
    
    def unregister_hook(
        self,
        hook_point: HookPoint,
        hook_id: str
    ) -> bool:
        """注销Hook
        
        Args:
            hook_point: Hook点
            hook_id: Hook ID
            
        Returns:
            bool: 是否成功注销
        """
        if hook_point not in self._hooks:
            return False
        
        for i, registration in enumerate(self._hooks[hook_point]):
            if registration.hook.hook_id == hook_id:
                self._hooks[hook_point].pop(i)
                if hook_id in self._hook_dict:
                    del self._hook_dict[hook_id]
                self._logger.debug(f"Hook {hook_id} 已从 {hook_point.value} 点注销")
                return True
        
        return False
    
    def get_hooks_for_point(self, hook_point: HookPoint) -> List[IHook]:
        """获取指定Hook点的所有Hook
        
        Args:
            hook_point: Hook点
            
        Returns:
            List[IHook]: Hook列表
        """
        if hook_point not in self._hooks:
            return []
        
        return [registration.hook for registration in self._hooks[hook_point]]
    
    def get_hook(self, hook_id: str) -> Optional[IHook]:
        """根据Hook ID获取Hook
        
        Args:
            hook_id: Hook ID
            
        Returns:
            Optional[IHook]: Hook实例，如果不存在则返回None
        """
        return self._hook_dict.get(hook_id)
    
    def clear_hooks(self, hook_point: Optional[HookPoint] = None) -> None:
        """清除Hook
        
        Args:
            hook_point: 要清除的Hook点，如果为None则清除所有
        """
        if hook_point is None:
            self._hooks.clear()
            self._hook_dict.clear()
            self._logger.debug("已清除所有Hook")
        else:
            if hook_point in self._hooks:
                # 从字典中移除相关Hook
                for registration in self._hooks[hook_point]:
                    if registration.hook.hook_id in self._hook_dict:
                        del self._hook_dict[registration.hook.hook_id]
                
                del self._hooks[hook_point]
                self._logger.debug(f"已清除 {hook_point.value} 点的所有Hook")
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        stats = {
            "total_hooks": len(self._hook_dict),
            "hook_points": {}
        }
        
        for hook_point, registrations in self._hooks.items():
            stats["hook_points"][hook_point.value] = len(registrations)
        
        return stats
    
    def list_all_hooks(self) -> List[Dict[str, Any]]:
        """列出所有Hook的信息
        
        Returns:
            List[Dict[str, Any]]: Hook信息列表
        """
        hooks_info = []
        
        for hook_point, registrations in self._hooks.items():
            for registration in registrations:
                hook = registration.hook
                hooks_info.append({
                    "hook_id": hook.hook_id,
                    "name": hook.name,
                    "description": hook.description,
                    "version": hook.version,
                    "hook_point": hook_point.value,
                    "priority": registration.priority,
                    "registered_at": registration.registered_at,
                    "supported_hook_points": [hp.value for hp in hook.get_supported_hook_points()]
                })
        
        return hooks_info
    
    def get_hook_points(self) -> List[HookPoint]:
        """获取所有已注册Hook的点
        
        Returns:
            List[HookPoint]: Hook点列表
        """
        return list(self._hooks.keys())
    
    def get_hooks_by_priority(self, hook_point: HookPoint, min_priority: int = 0, max_priority: int = 100) -> List[IHook]:
        """根据优先级范围获取Hook
        
        Args:
            hook_point: Hook点
            min_priority: 最小优先级
            max_priority: 最大优先级
            
        Returns:
            List[IHook]: 符合优先级范围的Hook列表
        """
        if hook_point not in self._hooks:
            return []
        
        return [
            registration.hook 
            for registration in self._hooks[hook_point]
            if min_priority <= registration.priority <= max_priority
        ]
    
    def validate_hook_dependencies(self) -> List[str]:
        """验证Hook依赖关系
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        for hook_point, registrations in self._hooks.items():
            for registration in registrations:
                hook = registration.hook
                
                # 检查Hook是否支持当前Hook点
                supported_points = hook.get_supported_hook_points()
                if hook_point not in supported_points:
                    errors.append(f"Hook {hook.hook_id} 不支持 Hook点 {hook_point.value}")
                
                # 检查Hook版本兼容性
                if hasattr(hook, 'min_version') and hasattr(hook, 'max_version'):
                    # 这里可以添加版本兼容性检查逻辑
                    pass
        
        return errors
    
    def get_hook_execution_order(self, hook_point: HookPoint) -> List[str]:
        """获取Hook执行顺序
        
        Args:
            hook_point: Hook点
            
        Returns:
            List[str]: Hook ID列表，按执行顺序排列
        """
        if hook_point not in self._hooks:
            return []
        
        return [registration.hook.hook_id for registration in self._hooks[hook_point]]
    
    def register(self, name: str, item: Any) -> None:
        """注册项目（基类方法实现）
        
        Args:
            name: 项目名称（Hook ID）
            item: Hook实例
            
        Note:
            对于Hook注册表，建议使用 register_hook 方法以获得更好的类型安全
        """
        if not isinstance(item, IHook):
            raise ValueError("项目必须实现 IHook 接口")
        
        # 尝试确定Hook点，如果无法确定则使用默认值
        supported_points = item.get_supported_hook_points()
        if supported_points:
            hook_point = supported_points[0]  # 使用第一个支持的Hook点
            self.register_hook(hook_point, item)
        else:
            # 如果没有支持的Hook点，则跳过注册（Hook必须支持至少一个Hook点）
            self._logger.warning(f"Hook {item.hook_id} 没有支持的Hook点，跳过注册")
    
    def get(self, name: str) -> Optional[Any]:
        """获取项目（基类方法实现）
        
        Args:
            name: 项目名称（Hook ID）
            
        Returns:
            Optional[Any]: Hook实例
        """
        return self.get_hook(name)
    
    def unregister(self, name: str) -> bool:
        """注销项目（基类方法实现）
        
        Args:
            name: 项目名称（Hook ID）
            
        Returns:
            bool: 是否成功注销
        """
        # 需要找到Hook所属的Hook点
        for hook_point, registrations in self._hooks.items():
            for registration in registrations:
                if registration.hook.hook_id == name:
                    return self.unregister_hook(hook_point, name)
        return False
    
    def list_items(self) -> List[str]:
        """列出所有项目名称（基类方法实现）
        
        Returns:
            List[str]: Hook ID列表
        """
        return list(self._hook_dict.keys())
    
    def clear(self) -> None:
        """清除所有项目（基类方法实现）"""
        self.clear_hooks()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息（基类方法实现）
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = super().get_stats()
        stats.update(self.get_registry_stats())
        return stats
    
    def validate_item(self, name: str, item: Any) -> None:
        """验证项目（基类方法实现）
        
        Args:
            name: 项目名称
            item: 项目对象
            
        Raises:
            ValueError: 项目验证失败
        """
        super().validate_item(name, item)
        
        if not isinstance(item, IHook):
            raise ValueError("项目必须实现 IHook 接口")
        
        if not hasattr(item, 'hook_id') or not item.hook_id:
            raise ValueError("Hook必须具有有效的hook_id属性")
        
        if not hasattr(item, 'get_supported_hook_points') or not callable(item.get_supported_hook_points):
            raise ValueError("Hook必须实现get_supported_hook_points方法")