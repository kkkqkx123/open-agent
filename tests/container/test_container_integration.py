"""
容器集成测试
"""

import pytest
from src.infrastructure.container.bootstrap import ContainerBootstrap
from src.interfaces.logger import ILogger
from src.interfaces.config import IConfigLoader
from src.interfaces.workflow import IWorkflowService
from src.interfaces.storage import IStorageService
from src.interfaces.llm import ILLMService

def test_full_container_integration():
    """测试完整的容器集成"""
    config = {
        "log_level": "INFO",
        "database_url": "postgresql://localhost:5432/app"
    }
    
    # 创建容器
    container = ContainerBootstrap.create_container(config)
    
    # 验证所有服务都已注册
    assert container.has_service(ILogger)
    assert container.has_service(IConfigLoader)
    assert container.has_service(IWorkflowService)
    assert container.has_service(IStorageService)
    assert container.has_service(ILLMService)
    
    # 获取所有服务
    logger = container.get(ILogger)
    config_loader = container.get(IConfigLoader)
    workflow_service = container.get(IWorkflowService)
    storage_service = container.get(IStorageService)
    llm_service = container.get(ILLMService)
    
    # 验证服务不为None
    assert logger is not None
    assert config_loader is not None
    assert workflow_service is not None
    assert storage_service is not None
    assert llm_service is not None

def test_service_lifecycle():
    """测试服务生命周期"""
    config = {}
    
    # 创建容器
    container = ContainerBootstrap.create_container(config)
    
    # 获取两次日志服务
    logger1 = container.get(ILogger)
    logger2 = container.get(ILogger)
    
    # 应该是同一个实例（单例）
    assert logger1 is logger2
    
    # 获取两次配置加载器
    config_loader1 = container.get(IConfigLoader)
    config_loader2 = container.get(IConfigLoader)
    
    # 应该是同一个实例（单例）
    assert config_loader1 is config_loader2

def test_container_with_custom_config():
    """测试使用自定义配置的容器"""
    config = {
        "log_level": "DEBUG",
        "custom_setting": "value"
    }
    
    # 创建容器
    container = ContainerBootstrap.create_container(config)
    
    # 获取日志服务
    logger = container.get(ILogger)
    
    # 验证服务不为None
    assert logger is not None