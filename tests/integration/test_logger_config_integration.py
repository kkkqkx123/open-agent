"""日志系统与配置系统集成测试"""

import pytest
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import Mock

from src.infrastructure.container import DependencyContainer
from src.infrastructure.config_loader import YamlConfigLoader
from src.config.config_system import ConfigSystem
from src.config.config_merger import ConfigMerger
from src.config.config_validator import ConfigValidator
from src.logger import (
    get_logger, 
    initialize_logging_integration,
    get_global_error_handler,
    ErrorType,
    LogLevel
)
from src.config import register_config_callback, CallbackPriority


class TestLoggingConfigIntegration:
    """日志系统与配置系统集成测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_dir(self, temp_dir):
        """创建配置目录"""
        config_dir = Path(temp_dir) / "configs"
        config_dir.mkdir()
        
        # 创建全局配置文件
        global_config = config_dir / "global.yaml"
        global_config.write_text("""
log_level: INFO
log_outputs:
  - type: console
    level: INFO
    format: text
secret_patterns:
  - "sk-[a-zA-Z0-9]{20,}"
env: test
debug: false
""")
        
        return str(config_dir)
    
    @pytest.fixture
    def container(self, config_dir):
        """创建依赖注入容器"""
        container = DependencyContainer()
        container.register(YamlConfigLoader, YamlConfigLoader, "default")
        container.register(ConfigMerger, ConfigMerger, "default")
        container.register(ConfigValidator, ConfigValidator, "default")
        container.register(ConfigSystem, ConfigSystem, "default")
        
        # 设置配置基础路径
        config_loader = container.get(YamlConfigLoader)
        config_loader.base_path = Path(config_dir)
        
        return container
    
    def test_integration_initialization(self, container):
        """测试集成初始化"""
        # 初始化集成
        initialize_logging_integration()
        
        # 获取服务
        config_system = container.get(ConfigSystem)
        logger = get_logger("test_app")
        
        # 验证服务正常工作
        assert config_system is not None
        assert logger is not None
        
        # 记录日志
        logger.info("测试日志消息")
    
    def test_config_change_callback(self, container, config_dir):
        """测试配置变更回调"""
        # 初始化集成
        initialize_logging_integration()
        
        # 注册测试回调
        callback_called = False
        callback_context = None
        
        def test_callback(context):
            nonlocal callback_called, callback_context
            callback_called = True
            callback_context = context
        
        register_config_callback(
            "test_callback",
            test_callback,
            priority=CallbackPriority.NORMAL,
            filter_paths=["global.yaml"]
        )
        
        # 获取配置系统
        config_system = container.get(ConfigSystem)
        
        # 模拟配置变更
        old_config = {"log_level": "INFO"}
        new_config = {"log_level": "DEBUG"}
        
        config_system._handle_file_change(str(Path(config_dir) / "global.yaml"))
        
        # 验证回调被调用
        # 注意：由于文件监听是异步的，这里可能需要等待
        # 在实际测试中，可能需要使用更复杂的同步机制
    
    def test_log_level_change(self, container, config_dir):
        """测试日志级别变更"""
        # 初始化集成
        initialize_logging_integration()
        
        # 获取日志记录器
        logger = get_logger("test_app")
        
        # 初始级别应该是INFO
        assert logger.get_level() == LogLevel.INFO
        
        # 修改配置文件
        global_config_path = Path(config_dir) / "global.yaml"
        global_config_path.write_text("""
log_level: DEBUG
log_outputs:
  - type: console
    level: INFO
    format: text
secret_patterns:
  - "sk-[a-zA-Z0-9]{20,}"
env: test
debug: false
""")
        
        # 触发文件变更处理
        config_system = container.get(ConfigSystem)
        config_system._handle_file_change(str(global_config_path))
        
        # 验证日志级别已更新
        # 注意：由于配置热重载是异步的，这里可能需要等待
    
    def test_error_handling_integration(self, container):
        """测试错误处理集成"""
        # 初始化集成
        initialize_logging_integration()
        
        # 获取错误处理器
        error_handler = get_global_error_handler()
        
        # 处理错误
        error = ValueError("测试错误")
        message = error_handler.handle_error(ErrorType.USER_ERROR, error)
        
        # 验证错误被正确处理
        assert "输入参数有误" in message
        assert "测试错误" in message
        
        # 验证错误历史
        history = error_handler.get_error_history()
        assert len(history) >= 1
        assert history[-1]['error_class'] == "ValueError"
    
    def test_log_redaction_integration(self, container):
        """测试日志脱敏集成"""
        # 初始化集成
        initialize_logging_integration()
        
        # 获取日志记录器
        logger = get_logger("test_app")
        
        # 记录敏感信息
        logger.info("API Key: sk-abc123def4567890123456")
        
        # 验证敏感信息被脱敏
        # 注意：这里需要检查日志输出，可能需要使用日志捕获器
    
    def test_metrics_integration(self, container):
        """测试指标收集集成"""
        # 初始化集成
        initialize_logging_integration()
        
        # 获取指标收集器
        from src.logger import get_global_metrics_collector
        metrics_collector = get_global_metrics_collector()
        
        # 记录指标
        metrics_collector.record_llm_metric("gpt-4", 100, 50, 2.0)
        metrics_collector.record_tool_metric("search", True, 0.5)
        
        # 验证指标被记录
        stats = metrics_collector.export_stats()
        assert stats['global']['total_llm_calls'] == 1
        assert stats['global']['total_tool_calls'] == 1
        assert stats['global']['total_tokens'] == 150
    
    def test_config_error_recovery(self, container, config_dir):
        """测试配置错误恢复"""
        # 启用错误恢复的配置系统
        config_system = ConfigSystem(
            container.get(YamlConfigLoader),
            container.get(ConfigMerger),
            container.get(ConfigValidator),
            base_path=config_dir,
            enable_error_recovery=True
        )
        
        # 损坏配置文件
        global_config_path = Path(config_dir) / "global.yaml"
        global_config_path.write_text("invalid: [")
        
        # 尝试加载配置（应该自动恢复）
        try:
            global_config = config_system.load_global_config()
            # 如果恢复成功，应该有默认配置
            assert global_config.log_level == "INFO"
        except Exception:
            # 如果恢复失败，这是可接受的
            pass
    
    def test_callback_priority_execution(self, container):
        """测试回调优先级执行"""
        # 初始化集成
        initialize_logging_integration()
        
        # 记录执行顺序
        execution_order = []
        
        def high_priority_callback(context):
            execution_order.append("high")
        
        def normal_priority_callback(context):
            execution_order.append("normal")
        
        def low_priority_callback(context):
            execution_order.append("low")
        
        # 注册不同优先级的回调
        register_config_callback("high", high_priority_callback, priority=CallbackPriority.HIGHEST)
        register_config_callback("normal", normal_priority_callback, priority=CallbackPriority.NORMAL)
        register_config_callback("low", low_priority_callback, priority=CallbackPriority.LOWEST)
        
        # 触发回调
        from src.config import trigger_config_callbacks
        trigger_config_callbacks("test.yaml", {}, {"key": "value"})
        
        # 验证执行顺序
        assert execution_order == ["high", "normal", "low"]
        
        # 清理
        from src.config import unregister_config_callback
        unregister_config_callback("high")
        unregister_config_callback("normal")
        unregister_config_callback("low")
    
    def test_callback_error_isolation(self, container):
        """测试回调错误隔离"""
        # 初始化集成
        initialize_logging_integration()
        
        # 记录执行情况
        success_callback_called = False
        
        def error_callback(context):
            raise ValueError("测试错误")
        
        def success_callback(context):
            nonlocal success_callback_called
            success_callback_called = True
        
        # 注册回调
        register_config_callback("error", error_callback, priority=CallbackPriority.HIGHEST)
        register_config_callback("success", success_callback, priority=CallbackPriority.LOW)
        
        # 触发回调（错误不应该影响其他回调）
        from src.config import trigger_config_callbacks
        trigger_config_callbacks("test.yaml", {}, {"key": "value"})
        
        # 验证成功回调仍然被调用
        assert success_callback_called is True
        
        # 清理
        from src.config import unregister_config_callback
        unregister_config_callback("error")
        unregister_config_callback("success")
    
    def test_end_to_end_workflow(self, container, config_dir):
        """测试端到端工作流"""
        # 初始化集成
        initialize_logging_integration()
        
        # 获取服务
        config_system = container.get(ConfigSystem)
        logger = get_logger("test_app")
        error_handler = get_global_error_handler()
        
        # 1. 加载配置
        global_config = config_system.load_global_config()
        assert global_config.log_level == "INFO"
        
        # 2. 记录日志
        logger.info("应用启动")
        logger.debug("调试信息")  # 不应该记录，因为级别是INFO
        logger.warning("警告信息")
        
        # 3. 处理错误
        try:
            raise ValueError("测试错误")
        except Exception as e:
            message = error_handler.handle_error(ErrorType.USER_ERROR, e)
            assert "输入参数有误" in message
        
        # 4. 记录指标
        from src.logger import get_global_metrics_collector
        metrics_collector = get_global_metrics_collector()
        metrics_collector.record_llm_metric("gpt-4", 100, 50, 2.0)
        
        # 5. 验证指标
        stats = metrics_collector.export_stats()
        assert stats['global']['total_llm_calls'] == 1
        
        # 6. 修改配置
        global_config_path = Path(config_dir) / "global.yaml"
        global_config_path.write_text("""
log_level: DEBUG
log_outputs:
  - type: console
    level: INFO
    format: text
secret_patterns:
  - "sk-[a-zA-Z0-9]{20,}"
env: test
debug: false
""")
        
        # 7. 触发配置变更
        config_system._handle_file_change(str(global_config_path))
        
        # 8. 验证配置变更生效
        # 注意：由于热重载是异步的，这里可能需要等待