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
from src.services.container.bindings.session_bindings import SessionServiceBindings
from src.services.container.bindings.thread_bindings import ThreadServiceBindings
from src.services.container.bindings.prompts_bindings import PromptsServiceBindings
from src.services.container.bindings.history_bindings import HistoryServiceBindings
from src.services.container.bindings.validation_bindings import ValidationServiceBindings

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

def test_session_service_bindings():
    """测试会话服务绑定"""
    from src.interfaces.sessions import ISessionService
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册会话服务
    session_bindings = SessionServiceBindings()
    session_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(ISessionService)
    
    # 获取服务
    session_service = container.get(ISessionService)
    assert session_service is not None

def test_thread_service_bindings():
    """测试线程服务绑定"""
    from src.interfaces.threads import IThreadService
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册线程服务
    thread_bindings = ThreadServiceBindings()
    thread_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(IThreadService)
    
    # 获取服务
    thread_service = container.get(IThreadService)
    assert thread_service is not None

def test_prompts_service_bindings():
    """测试提示词服务绑定"""
    from src.interfaces.prompts import IPromptLoader
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册提示词服务
    prompts_bindings = PromptsServiceBindings()
    prompts_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(IPromptLoader)
    
    # 获取服务
    prompt_loader = container.get(IPromptLoader)
    assert prompt_loader is not None

def test_history_service_bindings():
    """测试历史服务绑定"""
    from src.interfaces.history import IHistoryManager
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册历史服务
    history_bindings = HistoryServiceBindings()
    history_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(IHistoryManager)
    
    # 获取服务
    history_manager = container.get(IHistoryManager)
    assert history_manager is not None

def test_validation_service_bindings():
    """测试验证服务绑定"""
    from src.interfaces.config import IConfigValidator
    
    # 创建容器
    container = ContainerBootstrap.create_container({})
    
    # 注册验证服务
    validation_bindings = ValidationServiceBindings()
    validation_bindings.register_services(container, {})
    
    # 验证服务已注册
    assert container.has_service(IConfigValidator)
    
    # 获取服务
    config_validator = container.get(IConfigValidator)
    assert config_validator is not None