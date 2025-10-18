# 第一阶段测试策略与验收标准

## 1. 测试策略概述

第一阶段测试策略采用分层测试方法，确保基础设施模块的质量和稳定性。测试覆盖单元测试、集成测试和端到端测试，目标实现90%以上的代码覆盖率。

## 2. 测试框架配置

### 2.1 pytest 配置 (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=src 
    --cov-report=html:cov_html 
    --cov-report=term
    --cov-report=xml:cov.xml
    --cov-fail-under=90
    --strict-markers
    --strict-config
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

### 2.2 测试依赖 (pyproject.toml)

```toml
[project.optional-dependencies]
test = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.10.0",
    "pytest-benchmark>=4.0.0",
    "hypothesis>=6.0.0",
    "freezegun>=1.2.0",
]
```

## 3. 单元测试策略

### 3.1 基础设施模块单元测试

#### 3.1.1 依赖注入容器测试

```python
# tests/unit/infrastructure/test_container.py
import pytest
from src.infrastructure.container import DependencyContainer
from src.infrastructure.config_loader import IConfigLoader, YamlConfigLoader
from src.infrastructure.exceptions import ServiceNotRegisteredError


class TestDependencyContainer:
    def test_register_and_get_service(self):
        """测试服务注册和获取"""
        container = DependencyContainer()
        container.register(IConfigLoader, YamlConfigLoader)
        
        service = container.get(IConfigLoader)
        assert isinstance(service, YamlConfigLoader)
    
    def test_service_not_registered(self):
        """测试未注册服务异常"""
        container = DependencyContainer()
        
        with pytest.raises(ServiceNotRegisteredError):
            container.get(IConfigLoader)
    
    def test_environment_specific_registration(self):
        """测试环境特定注册"""
        container = DependencyContainer()
        
        class DevConfigLoader:
            pass
        
        class ProdConfigLoader:
            pass
        
        container.register(IConfigLoader, DevConfigLoader, "development")
        container.register(IConfigLoader, ProdConfigLoader, "production")
        
        container.set_environment("development")
        service = container.get(IConfigLoader)
        assert isinstance(service, DevConfigLoader)
        
        container.set_environment("production")
        service = container.get(IConfigLoader)
        assert isinstance(service, ProdConfigLoader)
```

#### 3.1.2 配置加载器测试

```python
# tests/unit/infrastructure/test_config_loader.py
import pytest
from unittest.mock import mock_open, patch
from src.infrastructure.config_loader import YamlConfigLoader


class TestYamlConfigLoader:
    def test_load_valid_yaml(self):
        """测试加载有效YAML配置"""
        yaml_content = """
        log_level: INFO
        log_outputs:
          - type: console
            level: INFO
        """
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            loader = YamlConfigLoader()
            config = loader.load("test.yaml")
            
            assert config["log_level"] == "INFO"
            assert len(config["log_outputs"]) == 1
    
    def test_resolve_env_vars(self):
        """测试环境变量解析"""
        import os
        os.environ["TEST_API_KEY"] = "secret_key"
        
        loader = YamlConfigLoader()
        config = {"api_key": "${TEST_API_KEY}", "port": "${TEST_PORT:8000}"}
        
        resolved = loader.resolve_env_vars(config)
        assert resolved["api_key"] == "secret_key"
        assert resolved["port"] == "8000"
    
    def test_env_var_not_found(self):
        """测试环境变量未找到"""
        loader = YamlConfigLoader()
        config = {"api_key": "${NONEXISTENT_VAR}"}
        
        with pytest.raises(EnvironmentError):
            loader.resolve_env_vars(config)
```

### 3.2 配置系统单元测试

#### 3.2.1 配置合并测试

```python
# tests/unit/config/test_config_merger.py
import pytest
from src.config.config_merger import ConfigMerger


class TestConfigMerger:
    def test_simple_merge(self):
        """测试简单配置合并"""
        merger = ConfigMerger()
        group_config = {"base_url": "https://api.example.com", "timeout": 30}
        individual_config = {"timeout": 60, "model": "gpt-4"}
        
        result = merger.merge_group_config(group_config, individual_config)
        
        assert result["base_url"] == "https://api.example.com"
        assert result["timeout"] == 60  # 个体配置覆盖
        assert result["model"] == "gpt-4"  # 新增字段
    
    def test_deep_merge_nested_dicts(self):
        """测试嵌套字典深度合并"""
        merger = ConfigMerger()
        dict1 = {"headers": {"User-Agent": "Agent/1.0"}, "params": {"a": 1}}
        dict2 = {"headers": {"Content-Type": "application/json"}, "params": {"b": 2}}
        
        result = merger.deep_merge(dict1, dict2)
        
        assert result["headers"]["User-Agent"] == "Agent/1.0"
        assert result["headers"]["Content-Type"] == "application/json"
        assert result["params"] == {"a": 1, "b": 2}
    
    def test_merge_with_inheritance(self):
        """测试配置继承"""
        merger = ConfigMerger()
        group_configs = {
            "openai_group": {
                "base_url": "https://api.openai.com/v1",
                "headers": {"User-Agent": "Agent/1.0"}
            }
        }
        individual_config = {"group": "openai_group", "model": "gpt-4"}
        
        result = merger.resolve_inheritance(individual_config, "llms", group_configs)
        
        assert result["base_url"] == "https://api.openai.com/v1"
        assert result["headers"]["User-Agent"] == "Agent/1.0"
        assert result["model"] == "gpt-4"
```

#### 3.2.2 配置验证测试

```python
# tests/unit/config/test_config_validator.py
import pytest
from pydantic import ValidationError
from src.config.config_validator import ConfigValidator
from src.config.models.global_config import GlobalConfig


class TestConfigValidator:
    def test_valid_global_config(self):
        """测试有效全局配置验证"""
        validator = ConfigValidator()
        config = {
            "log_level": "INFO",
            "log_outputs": [
                {"type": "console", "level": "INFO", "format": "text"}
            ],
            "secret_patterns": ["sk-.*"],
            "env": "development"
        }
        
        result = validator.validate_global_config(config)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_log_level(self):
        """测试无效日志级别验证"""
        validator = ConfigValidator()
        config = {
            "log_level": "INVALID_LEVEL",
            "log_outputs": [],
            "secret_patterns": []
        }
        
        result = validator.validate_global_config(config)
        assert not result.is_valid
        assert "log_level" in str(result.errors[0])
    
    def test_missing_required_field(self):
        """测试缺失必需字段验证"""
        validator = ConfigValidator()
        config = {
            "log_outputs": []
            # 缺少 log_level 和 secret_patterns
        }
        
        result = validator.validate_global_config(config)
        assert not result.is_valid
        assert any("log_level" in error for error in result.errors)
```

### 3.3 日志系统单元测试

#### 3.3.1 日志记录器测试

```python
# tests/unit/logging/test_logger.py
import pytest
from unittest.mock import Mock, patch
from src.logging.logger import Logger, LogLevel
from src.config.models.global_config import GlobalConfig


class TestLogger:
    @pytest.fixture
    def mock_config(self):
        return GlobalConfig(
            log_level="INFO",
            log_outputs=[
                {"type": "console", "level": "INFO", "format": "text"}
            ],
            secret_patterns=["sk-.*"],
            env="development",
            debug=False
        )
    
    def test_log_level_filtering(self, mock_config):
        """测试日志级别过滤"""
        mock_handler = Mock()
        logger = Logger(mock_config, Mock())
        logger._handlers = [mock_handler]
        
        # DEBUG 级别不应记录（配置为 INFO）
        logger.debug("Debug message")
        mock_handler.handle.assert_not_called()
        
        # INFO 级别应该记录
        logger.info("Info message")
        mock_handler.handle.assert_called_once()
    
    def test_log_redaction(self, mock_config):
        """测试日志脱敏"""
        mock_handler = Mock()
        mock_redactor = Mock()
        mock_redactor.redact.return_value = "Redacted message"
        
        logger = Logger(mock_config, mock_redactor)
        logger._handlers = [mock_handler]
        
        logger.info("Original message with sk-abc123")
        
        # 验证脱敏器被调用
        mock_redactor.redact.assert_called_once_with("Original message with sk-abc123", LogLevel.INFO)
        mock_handler.handle.assert_called_once_with(LogLevel.INFO, "Redacted message", {})
```

#### 3.3.2 指标收集器测试

```python
# tests/unit/logging/test_metrics.py
import pytest
import time
from src.logging.metrics import MetricsCollector


class TestMetricsCollector:
    def test_llm_metric_recording(self):
        """测试LLM指标记录"""
        collector = MetricsCollector()
        
        collector.record_llm_metric("gpt-4", 100, 50, 1.5)
        collector.record_llm_metric("gpt-4", 200, 100, 2.0)
        
        stats = collector.export_stats("test_session")
        llm_metrics = stats["llm_calls"]
        
        assert len(llm_metrics) == 1
        assert llm_metrics[0]["model"] == "gpt-4"
        assert llm_metrics[0]["count"] == 2
        assert llm_metrics[0]["input_tokens"] == 300
        assert llm_metrics[0]["output_tokens"] == 150
        assert llm_metrics[0]["total_time"] == 3.5
    
    def test_tool_metric_recording(self):
        """测试工具指标记录"""
        collector = MetricsCollector()
        
        collector.record_tool_metric("search_tool", True, 0.5)
        collector.record_tool_metric("search_tool", False, 0.3)
        
        stats = collector.export_stats("test_session")
        tool_metrics = stats["tool_calls"]
        
        search_metric = next(m for m in tool_metrics if m["tool"] == "search_tool")
        assert search_metric["count"] == 2
        assert search_metric["success_count"] == 1
        assert search_metric["total_time"] == 0.8
```

## 4. 集成测试策略

### 4.1 配置系统集成测试

```python
# tests/integration/test_config_integration.py
import pytest
import tempfile
import os
from src.infrastructure.container import DependencyContainer
from src.infrastructure.config_loader import YamlConfigLoader
from src.config.config_system import ConfigSystem
from src.config.config_merger import ConfigMerger
from src.config.config_validator import ConfigValidator


class TestConfigIntegration:
    def test_config_loading_integration(self):
        """测试配置加载集成"""
        # 创建临时配置文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建全局配置
            global_config_path = os.path.join(temp_dir, "global.yaml")
            with open(global_config_path, 'w') as f:
                f.write("""
                log_level: INFO
                log_outputs: []
                secret_patterns: []
                env: test
                """)
            
            # 创建LLM配置
            llm_dir = os.path.join(temp_dir, "llms")
            os.makedirs(llm_dir)
            
            group_config_path = os.path.join(llm_dir, "_group.yaml")
            with open(group_config_path, 'w') as f:
                f.write("""
                openai_group:
                  base_url: https://api.openai.com/v1
                  headers:
                    User-Agent: Agent/1.0
                """)
            
            individual_config_path = os.path.join(llm_dir, "gpt4.yaml")
            with open(individual_config_path, 'w') as f:
                f.write("""
                group: openai_group
                model_type: openai
                model_name: gpt-4
                """)
            
            # 初始化配置系统
            container = DependencyContainer()
            container.register(YamlConfigLoader, YamlConfigLoader)
            container.register(ConfigMerger, ConfigMerger)
            container.register(ConfigValidator, ConfigValidator)
            
            config_loader = container.get(YamlConfigLoader)
            config_merger = container.get(ConfigMerger)
            config_validator = container.get(ConfigValidator)
            
            config_system = ConfigSystem(config_loader, config_merger, config_validator)
            
            # 测试配置加载
            llm_config = config_system.load_llm_config("gpt4")
            assert llm_config.base_url == "https://api.openai.com/v1"
            assert llm_config.model_name == "gpt-4"
```

### 4.2 日志系统集成测试

```python
# tests/integration/test_logging_integration.py
import pytest
import tempfile
import json
from src.infrastructure.container import DependencyContainer
from src.config.config_system import ConfigSystem
from src.logging.logger import Logger
from src.logging.metrics import MetricsCollector
from src.logging.redactor import LogRedactor


class TestLoggingIntegration:
    def test_logging_with_redaction(self):
        """测试日志记录与脱敏集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            
            # 创建配置
            config_data = {
                "log_level": "INFO",
                "log_outputs": [
                    {
                        "type": "file",
                        "level": "INFO",
                        "format": "json",
                        "path": log_file
                    }
                ],
                "secret_patterns": ["sk-.*"],
                "env": "test"
            }
            
            # 初始化组件
            container = DependencyContainer()
            # ... 注册相关服务
            
            logger = container.get(Logger)
            logger.info("API Key: sk-abc123def456")
            
            # 验证日志文件内容
            with open(log_file, 'r') as f:
                log_entry = json.loads(f.readline())
                assert "***" in log_entry["message"]  # 验证脱敏
```

## 5. 端到端测试策略

### 5.1 完整配置流程测试

```python
# tests/e2e/test_config_workflow.py
import pytest
import tempfile
import os
from src.infrastructure.container import DependencyContainer
from src.infrastructure.environment import EnvironmentChecker
from src.config.config_system import ConfigSystem
from src.logging.logger import Logger


class TestConfigWorkflow:
    def test_complete_config_workflow(self):
        """测试完整配置工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 设置环境
            os.environ["AGENT_OPENAI_KEY"] = "test_key"
            
            # 创建配置文件
            self._create_test_configs(temp_dir)
            
            # 初始化所有组件
            container = DependencyContainer()
            self._setup_container(container, temp_dir)
            
            # 环境检查
            env_checker = container.get(EnvironmentChecker)
            results = env_checker.check_dependencies()
            assert all(r.status == "PASS" for r in results)
            
            # 配置加载
            config_system = container.get(ConfigSystem)
            global_config = config_system.load_global_config()
            assert global_config.log_level == "INFO"
            
            # 日志记录
            logger = container.get(Logger)
            logger.info("系统启动完成")
            
            # 验证指标收集
            metrics = container.get(MetricsCollector)
            metrics.record_session_start("test_session")
            # ... 更多测试
    
    def _create_test_configs(self, temp_dir):
        """创建测试配置文件"""
        # 实现配置文件创建逻辑
        pass
    
    def _setup_container(self, container, config_dir):
        """设置依赖注入容器"""
        # 实现容器设置逻辑
        pass
```

## 6. 性能测试策略

### 6.1 配置加载性能测试

```python
# tests/performance/test_config_performance.py
import pytest
import time
from src.config.config_system import ConfigSystem


class TestConfigPerformance:
    @pytest.mark.benchmark
    def test_config_loading_performance(self, benchmark):
        """测试配置加载性能"""
        def load_config():
            config_system = ConfigSystem(...)
            return config_system.load_llm_config("gpt4")
        
        # 基准测试
        result = benchmark(load_config)
        assert result is not None
    
    @pytest.mark.benchmark
    def test_logging_performance(self, benchmark):
        """测试日志记录性能"""
        def log_messages():
            logger = Logger(...)
            for i in range(1000):
                logger.info(f"Test message {i}")
        
        # 基准测试
        benchmark(log_messages)
```

## 7. 验收标准

### 7.1 功能验收标准

**基础架构与环境配置模块：**
- [ ] 依赖注入容器正确注册和获取服务
- [ ] 环境检查工具能检测Python版本和依赖包
- [ ] 配置加载器能正确加载YAML文件和环境变量
- [ ] 架构分层检查工具能验证模块依赖关系

**配置系统模块：**
- [ ] 配置分组继承机制正常工作
- [ ] 环境变量注入和敏感信息脱敏正确
- [ ] 配置验证能捕获格式错误和缺失字段
- [ ] 热重载功能在开发环境有效

**日志与指标模块：**
- [ ] 分级日志系统按级别过滤消息
- [ ] 多目标输出（控制台、文件）正常工作
- [ ] 智能脱敏能隐藏敏感信息
- [ ] 指标收集能准确统计LLM和工具调用

### 7.2 性能验收标准

- [ ] 配置加载时间 < 100ms（冷启动）
- [ ] 配置加载时间 < 10ms（缓存后）
- [ ] 日志记录延迟 < 5ms
- [ ] 依赖注入服务获取 < 1ms
- [ ] 内存使用稳定，无内存泄漏

### 7.3 质量验收标准

- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 集成测试覆盖率 ≥ 80%
- [ ] 代码质量评分 ≥ A级（使用pylint、mypy）
- [ ] 所有测试用例通过率 100%
- [ ] 文档完整准确，包含使用示例

### 7.4 安全验收标准

- [ ] 敏感信息（API Key等）在日志中正确脱敏
- [ ] 环境变量注入机制安全可靠
- [ ] 配置验证能防止注入攻击
- [ ] 错误信息不泄露敏感数据

## 8. 测试报告

### 8.1 测试报告生成

```bash
# 生成HTML覆盖率报告
pytest --cov=src --cov-report=html:cov_html

# 生成JUnit XML报告（CI/CD集成）
pytest --junitxml=test-results.xml

# 生成性能基准报告
pytest --benchmark-json=benchmark-results.json tests/performance/
```

### 8.2 持续集成

在CI/CD流水线中集成以下检查：
- 单元测试执行和覆盖率检查
- 代码质量检查（pylint、mypy）
- 性能基准测试
- 安全扫描

这个测试策略确保了第一阶段基础设施模块的质量和稳定性，为后续开发奠定了坚实的基础。