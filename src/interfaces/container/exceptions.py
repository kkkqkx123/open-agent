"""
依赖注入容器异常定义

定义容器相关的异常类型和异常处理接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class ContainerException(Exception):
    """容器基础异常类"""
    
    def __init__(self, message: str, service_type: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.service_type = service_type
        self.context = context or {}
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.service_type:
            return f"{base_msg} (服务: {self.service_type})"
        return base_msg


class RegistrationError(ContainerException):
    """注册错误"""
    pass


class ServiceNotFoundError(ContainerException):
    """服务未找到错误"""
    pass


class ServiceCreationError(ContainerException):
    """服务创建错误"""
    pass


class CircularDependencyError(ContainerException):
    """循环依赖错误"""
    
    def __init__(self, message: str, dependency_chain: List[str]):
        super().__init__(message)
        self.dependency_chain = dependency_chain
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        chain_str = " -> ".join(self.dependency_chain)
        return f"{base_msg}\n依赖链: {chain_str}"


class ValidationError(ContainerException):
    """验证错误"""
    
    def __init__(self, message: str, validation_errors: List[str]):
        super().__init__(message)
        self.validation_errors = validation_errors
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        errors_str = "\n".join(f"  - {error}" for error in self.validation_errors)
        return f"{base_msg}\n验证错误:\n{errors_str}"


class IExceptionHandler(ABC):
    """异常处理器接口"""
    
    @abstractmethod
    def handle_registration_error(
        self, 
        error: RegistrationError, 
        service_type: str
    ) -> bool:
        """
        处理注册错误
        
        Args:
            error: 注册错误
            service_type: 服务类型
            
        Returns:
            bool: 是否已处理错误（True表示错误已被处理，不需要重新抛出）
        """
        pass
    
    @abstractmethod
    def handle_creation_error(
        self, 
        error: ServiceCreationError, 
        service_type: str
    ) -> bool:
        """
        处理创建错误
        
        Args:
            error: 创建错误
            service_type: 服务类型
            
        Returns:
            bool: 是否已处理错误（True表示错误已被处理，不需要重新抛出）
        """
        pass
    
    @abstractmethod
    def handle_circular_dependency_error(
        self, 
        error: CircularDependencyError
    ) -> bool:
        """
        处理循环依赖错误
        
        Args:
            error: 循环依赖错误
            
        Returns:
            bool: 是否已处理错误
        """
        pass
    
    @abstractmethod
    def handle_validation_error(
        self, 
        error: ValidationError
    ) -> bool:
        """
        处理验证错误
        
        Args:
            error: 验证错误
            
        Returns:
            bool: 是否已处理错误
        """
        pass


class DefaultExceptionHandler(IExceptionHandler):
    """默认异常处理器"""
    
    def __init__(self, use_system_output: bool = True):
        self.use_system_output = use_system_output
    
    def handle_registration_error(self, error: RegistrationError, service_type: str) -> bool:
        """处理注册错误"""
        if self.use_system_output:
            import sys
            print(f"[ERROR] 服务注册失败: {service_type} - {error}", file=sys.stderr)
        return False  # 不处理，继续抛出异常
    
    def handle_creation_error(self, error: ServiceCreationError, service_type: str) -> bool:
        """处理创建错误"""
        if self.use_system_output:
            import sys
            print(f"[ERROR] 服务创建失败: {service_type} - {error}", file=sys.stderr)
        return False  # 不处理，继续抛出异常
    
    def handle_circular_dependency_error(self, error: CircularDependencyError) -> bool:
        """处理循环依赖错误"""
        if self.use_system_output:
            import sys
            print(f"[ERROR] 循环依赖检测到: {error}", file=sys.stderr)
        return False  # 不处理，继续抛出异常
    
    def handle_validation_error(self, error: ValidationError) -> bool:
        """处理验证错误"""
        if self.use_system_output:
            import sys
            print(f"[ERROR] 配置验证失败: {error}", file=sys.stderr)
        return False  # 不处理，继续抛出异常