"""
服务绑定单元测试
"""

import pytest
from src.infrastructure.container.bootstrap import ContainerBootstrap
from src.services.container.bindings.logger_bindings import LoggerServiceBindings
from src.services.container.bindings.config_bindings import ConfigServiceBindings
from src.services.container.bindings.workflow_bindings import WorkflowServiceBindings
from src.services.container.bindings.storage_bindings import StorageServiceBindings
from src.services.container.bindings.llm_bindings import LLMServiceBindings

def test_logger_service_bindings():
    """测试日志服务绑定"""
    from src.interfaces.logger import ILogger
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册日志服务
    logger_bindings = LoggerServiceBindings()
    logger_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(ILogger)
    
    # 获取服务
    logger = container.get(ILogger)
    assert logger is not None

def test_config_service_bindings():
    """测试配置服务绑定"""
    from src.interfaces.config import IConfigLoader
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册配置服务
    config_bindings = ConfigServiceBindings()
    config_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(IConfigLoader)
    
    # 获取服务
    config_loader = container.get(IConfigLoader)
    assert config_loader is not None

def test_workflow_service_bindings():
    """测试工作流服务绑定"""
    from src.interfaces.workflow import IWorkflowService
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册工作流服务
    workflow_bindings = WorkflowServiceBindings()
    workflow_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(IWorkflowService)
    
    # 获取服务
    workflow_service = container.get(IWorkflowService)
    assert workflow_service is not None

def test_storage_service_bindings():
    """测试存储服务绑定"""
    from src.interfaces.storage import IStorageService
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册存储服务
    storage_bindings = StorageServiceBindings()
    storage_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(IStorageService)
    
    # 获取服务
    storage_service = container.get(IStorageService)
    assert storage_service is not None

def test_llm_service_bindings():
    """测试LLM服务绑定"""
    from src.interfaces.llm import ILLMService
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册LLM服务
    llm_bindings = LLMServiceBindings()
    llm_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(ILLMService)
    
    # 获取服务
    llm_service = container.get(ILLMService)
    assert llm_service is not None