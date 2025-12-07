"""Hook注册表

管理Hook的注册和获取。
"""

from typing import Dict, List, Optional, Any
from src.interfaces.workflow.hooks import IHook, IHookRegistry, HookPoint
from src.services.logger.injection import get_logger

logger = get_logger(__name__)


class HookRegistry(IHookRegistry):
    """Hook注册表实现
    
    管理所有Hook的注册、注销和获取。
    """
    
    def __init__(self):
        """初始化Hook注册表"""
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
                logger.warning(f"Hook {hook.hook_id} 已在 {hook_point.value} 点注册，将被覆盖")
                self._hooks[hook_point].remove(registration)
        
        registration = HookRegistration(hook, priority)
        self._hooks[hook_point].append(registration)
        self._hook_dict[hook.hook_id] = hook
        
        # 按优先级排序
        self._hooks[hook_point].sort(key=lambda r: r.priority)
        
        logger.debug(f"Hook {hook.hook_id} 已注册到 {hook_point.value} 点，优先级: {priority}")
    
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
                logger.debug(f"Hook {hook_id} 已从 {hook_point.value} 点注销")
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
            logger.debug("已清除所有Hook")
        else:
            if hook_point in self._hooks:
                # 从字典中移除相关Hook
                for registration in self._hooks[hook_point]:
                    if registration.hook.hook_id in self._hook_dict:
                        del self._hook_dict[registration.hook.hook_id]
                
                del self._hooks[hook_point]
                logger.debug(f"已清除 {hook_point.value} 点的所有Hook")
    
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
                    "supported_hook_points": [hp.value for hp in hook.get_supported_hook_points()]
                })
        
        return hooks_info


class HookRegistration:
    """Hook注册信息"""
    
    def __init__(self, hook: IHook, priority: int):
        """初始化Hook注册信息
        
        Args:
            hook: Hook实例
            priority: 优先级
        """
        self.hook = hook
        self.priority = priority