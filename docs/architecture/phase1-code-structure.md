# 第一阶段代码结构与目录规划

## 1. 项目整体结构

```
open-agent/
├── pyproject.toml              # 项目配置和依赖管理
├── README.md                   # 项目说明文档
├── .env.example                # 环境变量示例
├── .gitignore                  # Git忽略文件
├── configs/                    # 配置文件目录
│   ├── global.yaml            # 全局配置
│   ├── llms/                  # 模型配置
│   │   ├── _group.yaml        # 模型组配置
│   │   ├── gpt4.yaml          # GPT-4配置
│   │   └── gemini-pro.yaml    # Gemini配置
│   ├── agents/                # Agent配置
│   │   ├── _group.yaml        # Agent组配置
│   │   └── code_agent.yaml    # 代码Agent配置
│   ├── tool_sets/             # 工具集配置
│   │   └── data_analysis.yaml # 数据分析工具集
│   └── prompt_registry.yaml   # 提示词注册表
├── src/                        # 源代码目录
│   ├── __init__.py
│   ├── infrastructure/        # 基础设施层
│   ├── config/                # 配置系统
│   ├── logger/               # 日志与指标
│   └── common/                # 公共模块
├── tests/                     # 测试目录
│   ├── unit/                  # 单元测试
│   ├── integration/           # 集成测试
│   └── conftest.py            # 测试配置
├── docs/                      # 文档目录
│   ├── plan/                  # 实施计划
│   └── api/                   # API文档
├── prompts/                   # 提示词目录
│   ├── system/                # 系统提示词
│   ├── rules/                 # 规则提示词
│   └── user_commands/         # 用户指令
└── tools/                     # 工具目录（预留）
```

## 2. 源代码详细结构

### 2.1 基础设施层 (src/infrastructure/)

```
src/infrastructure/
├── __init__.py
├── container.py               # 依赖注入容器
├── config_loader.py           # 配置加载器
├── environment.py             # 环境检查工具
├── architecture.py            # 架构分层检查
├── exceptions.py              # 异常定义
└── types.py                   # 类型定义
```

### 2.2 配置系统 (src/config/)

```
src/config/
├── __init__.py
├── config_system.py           # 配置系统核心
├── config_merger.py           # 配置合并逻辑
├── config_validator.py        # 配置验证器
├── models/                    # Pydantic配置模型
│   ├── __init__.py
│   ├── base.py                # 基础配置模型
│   ├── global_config.py       # 全局配置模型
│   ├── llm_config.py          # LLM配置模型
│   ├── agent_config.py        # Agent配置模型
│   └── tool_config.py         # 工具配置模型
└── utils/                     # 配置工具
    ├── __init__.py
    ├── env_resolver.py        # 环境变量解析器
    ├── file_watcher.py        # 文件监听器
    └── schema_loader.py       # 配置模式加载器
```

### 2.3 日志与指标 (src/logger/)

```
src/logger/
├── __init__.py
├── logger.py                  # 日志记录器
├── metrics.py                 # 指标收集器
├── error_handler.py           # 全局错误处理器
├── redactor.py                # 日志脱敏器
├── handlers/                  # 日志处理器
│   ├── __init__.py
│   ├── base_handler.py        # 基础处理器
│   ├── console_handler.py     # 控制台处理器
│   ├── file_handler.py        # 文件处理器
│   └── json_handler.py        # JSON处理器
└── formatters/                # 日志格式化器
    ├── __init__.py
    ├── text_formatter.py      # 文本格式化器
    ├── json_formatter.py      # JSON格式化器
    └── color_formatter.py     # 彩色格式化器
```

### 2.4 公共模块 (src/common/)

```
src/common/
├── __init__.py
├── constants.py               # 常量定义
├── types.py                   # 公共类型定义
├── utils.py                   # 公共工具函数
└── decorators.py              # 装饰器
```

## 3. 核心文件详细说明

### 3.1 pyproject.toml

```toml
[project]
name = "modular-agent-framework"
version = "0.1.0"
description = "A modular agent framework based on LangGraph"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = [
    "python>=3.13",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
    "dependency-injector>=4.0.0",
    "rich>=13.0.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html:cov_html --cov-report=term"
asyncio_mode = "auto"

[tool.black]
line-length = 100
target-version = ['py313']
```

### 3.2 src/infrastructure/container.py

```python
"""依赖注入容器实现"""
from typing import Type, TypeVar, Dict, Any, Optional
from dependency_injector import containers, providers

T = TypeVar('T')

class DependencyContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._services = {}
        self._implementations = {}
        self._environment = "development"
    
    def register(self, interface: Type, implementation: Type, environment: str = "default") -> None:
        """注册服务实现"""
        if interface not in self._implementations:
            self._implementations[interface] = {}
        self._implementations[interface][environment] = implementation
    
    def get[T](self, service_type: Type[T]) -> T:
        """获取服务实例"""
        if service_type not in self._implementations:
            raise ServiceNotRegisteredError(f"Service {service_type} not registered")
        
        # 按环境查找实现
        env_impl = self._implementations[service_type]
        implementation = (env_impl.get(self._environment) or 
                         env_impl.get("default") or 
                         next(iter(env_impl.values())))
        
        if service_type not in self._services:
            self._services[service_type] = implementation()
        
        return self._services[service_type]
    
    def set_environment(self, env: str) -> None:
        """设置当前环境"""
        self._environment = env
        # 清除缓存，强制重新创建服务实例
        self._services.clear()
```

### 3.3 src/config/config_system.py

```python
"""配置系统核心实现"""
import os
from typing import Dict, Any, Optional
from pydantic import ValidationError

from .models.global_config import GlobalConfig
from .models.llm_config import LLMConfig
from .models.agent_config import AgentConfig
from ..infrastructure.container import IDependencyContainer
from ..infrastructure.config_loader import IConfigLoader
from .config_merger import IConfigMerger
from .config_validator import IConfigValidator


class ConfigSystem:
    """配置系统"""
    
    def __init__(
        self, 
        config_loader: IConfigLoader,
        config_merger: IConfigMerger,
        config_validator: IConfigValidator
    ):
        self._config_loader = config_loader
        self._config_merger = config_merger
        self._config_validator = config_validator
        self._cache = {}
        self._global_config = None
    
    def load_global_config(self) -> GlobalConfig:
        """加载全局配置"""
        if self._global_config is None:
            config_data = self._config_loader.load("configs/global.yaml")
            result = self._config_validator.validate_global_config(config_data)
            if not result.is_valid:
                raise ConfigValidationError(f"Global config validation failed: {result.errors}")
            self._global_config = GlobalConfig(**config_data)
        return self._global_config
    
    def load_llm_config(self, name: str) -> LLMConfig:
        """加载LLM配置"""
        cache_key = f"llm_{name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 加载配置并处理继承
        config_data = self._load_config_with_inheritance("llms", name)
        result = self._config_validator.validate_llm_config(config_data)
        if not result.is_valid:
            raise ConfigValidationError(f"LLM config validation failed: {result.errors}")
        
        config = LLMConfig(**config_data)
        self._cache[cache_key] = config
        return config
    
    def _load_config_with_inheritance(self, config_type: str, name: str) -> Dict[str, Any]:
        """加载配置并处理继承关系"""
        # 加载个体配置
        individual_path = f"configs/{config_type}/{name}.yaml"
        individual_config = self._config_loader.load(individual_path)
        
        # 检查是否有组配置
        if "group" in individual_config:
            group_name = individual_config["group"]
            group_path = f"configs/{config_type}/_group.yaml"
            group_configs = self._config_loader.load(group_path)
            
            if group_name in group_configs:
                group_config = group_configs[group_name]
                # 合并组配置和个体配置
                merged_config = self._config_merger.merge_group_config(
                    group_config, individual_config
                )
                return merged_config
        
        return individual_config
```

### 3.4 src/logger/logger.py

```python
"""日志记录器实现"""
import logging
import sys
from typing import Dict, Any, List, Optional
from enum import Enum

from .handlers.console_handler import ConsoleHandler
from .handlers.file_handler import FileHandler
from .redactor import LogRedactor
from ..config.models.global_config import GlobalConfig


class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Logger:
    """日志记录器"""
    
    def __init__(self, config: GlobalConfig, redactor: LogRedactor):
        self._config = config
        self._redactor = redactor
        self._handlers = []
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        for output_config in self._config.log_outputs:
            handler = self._create_handler(output_config)
            if handler:
                self._handlers.append(handler)
    
    def _create_handler(self, config: Dict[str, Any]):
        """创建日志处理器"""
        handler_type = config.get("type")
        level = getattr(LogLevel, config.get("level", "INFO").upper())
        
        if handler_type == "console":
            return ConsoleHandler(level, config)
        elif handler_type == "file":
            return FileHandler(level, config)
        else:
            return None
    
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """记录严重错误日志"""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        """内部日志记录方法"""
        if not self._should_log(level):
            return
        
        # 脱敏处理
        redacted_message = self._redactor.redact(message, level)
        redacted_kwargs = {
            k: self._redactor.redact(str(v), level) if isinstance(v, str) else v
            for k, v in kwargs.items()
        }
        
        # 发送到所有处理器
        for handler in self._handlers:
            handler.handle(level, redacted_message, **redacted_kwargs)
    
    def _should_log(self, level: LogLevel) -> bool:
        """检查是否应该记录日志"""
        current_level = LogLevel[self._config.log_level.upper()]
        return level.value >= current_level.value
```

## 4. 测试目录结构

```
tests/
├── unit/                      # 单元测试
│   ├── infrastructure/        # 基础设施测试
│   │   ├── test_container.py
│   │   ├── test_config_loader.py
│   │   └── test_environment.py
│   ├── config/               # 配置系统测试
│   │   ├── test_config_system.py
│   │   ├── test_config_merger.py
│   │   └── test_config_validator.py
│   └── logger/              # 日志系统测试
│       ├── test_logger.py
│       ├── test_metrics.py
│       └── test_error_handler.py
├── integration/              # 集成测试
│   ├── test_config_integration.py
│   ├── test_logger_integration.py
│   └── test_infrastructure_integration.py
├── fixtures/                 # 测试夹具
│   ├── config_fixtures.py
│   ├── logger_fixtures.py
│   └── infrastructure_fixtures.py
└── conftest.py              # 测试配置
```

## 5. 配置示例文件

### 5.1 configs/global.yaml

```yaml
# 全局配置
log_level: "INFO"
log_outputs:
  - type: "console"
    level: "INFO"
    format: "text"
  - type: "file"
    level: "DEBUG"
    format: "json"
    path: "logs/agent.log"
    rotation: "daily"
    max_size: "10MB"

secret_patterns:
  - "sk-[a-zA-Z0-9]{20,}"
  - "\\w+@\\w+\\.\\w+"
  - "1\\d{10}"

env: "development"
debug: true
env_prefix: "AGENT_"

# 热重载配置
hot_reload: true
watch_interval: 5  # 秒
```

### 5.2 configs/llms/_group.yaml

```yaml
# 模型组配置
openai_group:
  base_url: "https://api.openai.com/v1"
  headers:
    User-Agent: "ModularAgent/1.0"
  parameters:
    temperature: 0.7
    max_tokens: 2000
    top_p: 1.0

gemini_group:
  base_url: "https://generativelanguage.googleapis.com/v1"
  headers:
    User-Agent: "ModularAgent/1.0"
  parameters:
    temperature: 0.7
    max_tokens: 2048
```

### 5.3 configs/llms/gpt4.yaml

```yaml
# GPT-4配置
group: "openai_group"
model_type: "openai"
model_name: "gpt-4-turbo"
api_key: "${AGENT_OPENAI_KEY}"
parameters:
  temperature: 0.3
  top_p: 0.9
```

## 6. 开发指南

### 6.1 环境设置

```bash
# 创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e .

# 安装开发依赖
uv pip install -e ".[dev]"
```

### 6.2 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/unit/infrastructure/

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 6.3 代码质量检查

```bash
# 代码格式化
black src/ tests/

# 导入排序
isort src/ tests/

# 类型检查
mypy src/
```

这个代码结构设计确保了模块间的清晰分离，便于团队协作开发和维护。每个模块都有明确的职责边界，接口定义清晰，便于后续扩展和测试。