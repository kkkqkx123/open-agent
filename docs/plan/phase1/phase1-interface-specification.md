# 第一阶段接口规范与实现细节

## 1. 基础架构与环境配置模块

### 1.1 IDependencyContainer 接口

```python
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Dict, Any, Optional

T = TypeVar('T')

class IDependencyContainer(ABC):
    """依赖注入容器接口"""
    
    @abstractmethod
    def register(self, interface: Type, implementation: Type, environment: str = "default") -> None:
        """注册服务实现"""
        pass
    
    @abstractmethod
    def get[T](self, service_type: Type[T]) -> T:
        """获取服务实例"""
        pass
    
    @abstractmethod
    def get_environment(self) -> str:
        """获取当前环境"""
        pass
    
    @abstractmethod
    def set_environment(self, env: str) -> None:
        """设置当前环境"""
        pass
    
    @abstractmethod
    def has_service(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        pass
```

### 1.2 IConfigLoader 接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IConfigLoader(ABC):
    """配置加载器接口"""
    
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        pass
    
    @abstractmethod
    def reload(self) -> None:
        """重新加载所有配置"""
        pass
    
    @abstractmethod
    def watch_for_changes(self, callback: callable) -> None:
        """监听配置变化"""
        pass
    
    @abstractmethod
    def resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析环境变量"""
        pass
```

### 1.3 IEnvironmentChecker 接口

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class CheckResult:
    """环境检查结果"""
    component: str
    status: str  # "PASS", "WARNING", "ERROR"
    message: str
    details: Dict[str, Any]

class IEnvironmentChecker(ABC):
    """环境检查器接口"""
    
    @abstractmethod
    def check_dependencies(self) -> List[CheckResult]:
        """检查所有依赖"""
        pass
    
    @abstractmethod
    def check_python_version(self) -> CheckResult:
        """检查Python版本"""
        pass
    
    @abstractmethod
    def check_required_packages(self) -> List[CheckResult]:
        """检查必需包"""
        pass
    
    @abstractmethod
    def check_config_files(self) -> List[CheckResult]:
        """检查配置文件"""
        pass
```

## 2. 配置系统模块

### 2.1 IConfigSystem 接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class GlobalConfig(BaseModel):
    """全局配置模型"""
    log_level: str
    log_outputs: List[Dict[str, Any]]
    secret_patterns: List[str]
    env: str = "development"
    debug: bool = False

class LLMConfig(BaseModel):
    """LLM配置模型"""
    model_type: str
    model_name: str
    base_url: str
    api_key: str
    headers: Dict[str, str] = {}
    parameters: Dict[str, Any] = {}

class AgentConfig(BaseModel):
    """Agent配置模型"""
    name: str
    llm: str
    tool_sets: List[str] = []
    tools: List[str] = []
    system_prompt: str = ""
    rules: List[str] = []
    user_command: str = ""

class IConfigSystem(ABC):
    """配置系统接口"""
    
    @abstractmethod
    def load_global_config(self) -> GlobalConfig:
        """加载全局配置"""
        pass
    
    @abstractmethod
    def load_llm_config(self, name: str) -> LLMConfig:
        """加载LLM配置"""
        pass
    
    @abstractmethod
    def load_agent_config(self, name: str) -> AgentConfig:
        """加载Agent配置"""
        pass
    
    @abstractmethod
    def reload_configs(self) -> None:
        """重新加载所有配置"""
        pass
    
    @abstractmethod
    def get_config_path(self, config_type: str, name: str) -> str:
        """获取配置路径"""
        pass
```

### 2.2 IConfigMerger 接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class IConfigMerger(ABC):
    """配置合并器接口"""
    
    @abstractmethod
    def merge_group_config(self, group_config: Dict[str, Any], individual_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并组配置和个体配置"""
        pass
    
    @abstractmethod
    def deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        pass
    
    @abstractmethod
    def resolve_inheritance(self, config: Dict[str, Any], config_type: str) -> Dict[str, Any]:
        """解析配置继承"""
        pass
```

### 2.3 IConfigValidator 接口

```python
from abc import ABC, abstractmethod
from typing import Type, Any, List
from pydantic import BaseModel, ValidationError

class ValidationResult:
    """验证结果"""
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []

class IConfigValidator(ABC):
    """配置验证器接口"""
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any], model: Type[BaseModel]) -> ValidationResult:
        """验证配置"""
        pass
    
    @abstractmethod
    def validate_llm_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置"""
        pass
    
    @abstractmethod
    def validate_agent_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证Agent配置"""
        pass
    
    @abstractmethod
    def validate_global_config(self, config: Dict[str, Any]) -> ValidationResult:
        """验证全局配置"""
        pass
```

## 3. 日志与指标模块

### 3.1 ILogger 接口

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum

class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class ILogger(ABC):
    """日志记录器接口"""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """记录严重错误日志"""
        pass
    
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别"""
        pass
    
    @abstractmethod
    def add_handler(self, handler) -> None:
        """添加日志处理器"""
        pass
```

### 3.2 IMetricsCollector 接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime

class LLMMetric:
    """LLM指标数据"""
    def __init__(self, model: str, count: int, input_tokens: int, output_tokens: int, total_time: float):
        self.model = model
        self.count = count
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_time = total_time

class ToolMetric:
    """工具指标数据"""
    def __init__(self, tool: str, count: int, success_count: int, total_time: float):
        self.tool = tool
        self.count = count
        self.success_count = success_count
        self.total_time = total_time

class IMetricsCollector(ABC):
    """指标收集器接口"""
    
    @abstractmethod
    def record_llm_metric(self, model: str, input_tokens: int, output_tokens: int, duration: float) -> None:
        """记录LLM调用指标"""
        pass
    
    @abstractmethod
    def record_tool_metric(self, tool: str, success: bool, duration: float) -> None:
        """记录工具调用指标"""
        pass
    
    @abstractmethod
    def record_session_start(self, session_id: str) -> None:
        """记录会话开始"""
        pass
    
    @abstractmethod
    def record_session_end(self, session_id: str) -> None:
        """记录会话结束"""
        pass
    
    @abstractmethod
    def export_stats(self, session_id: str) -> Dict[str, Any]:
        """导出统计信息"""
        pass
```

### 3.3 IGlobalErrorHandler 接口

```python
from abc import ABC, abstractmethod
from typing import Type, Callable, Any
from enum import Enum

class ErrorType(Enum):
    USER_ERROR = "user_error"      # 用户错误（配置错误、参数无效）
    SYSTEM_ERROR = "system_error"  # 系统错误（LLM调用失败、工具超时）
    FATAL_ERROR = "fatal_error"    # 致命错误（内存不足、配置文件损坏）

class IGlobalErrorHandler(ABC):
    """全局错误处理器接口"""
    
    @abstractmethod
    def handle_error(self, error_type: ErrorType, error: Exception, context: Dict[str, Any] = None) -> str:
        """处理错误并返回用户友好消息"""
        pass
    
    @abstractmethod
    def register_error_handler(self, error_class: Type[Exception], handler: Callable) -> None:
        """注册自定义错误处理器"""
        pass
    
    @abstractmethod
    def wrap_with_error_handler(self, func: Callable) -> Callable:
        """用错误处理器包装函数"""
        pass
```

### 3.4 LogRedactor 类

```python
class LogRedactor:
    """日志脱敏器"""
    
    def __init__(self, patterns: List[str] = None):
        self.patterns = patterns or [
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI API Key
            r'\w+@\w+\.\w+',         # 邮箱地址
            r'1\d{10}',              # 手机号
        ]
    
    def redact(self, text: str, level: LogLevel) -> str:
        """脱敏文本"""
        if level == LogLevel.DEBUG:
            return text  # DEBUG级别不脱敏
        
        redacted_text = text
        for pattern in self.patterns:
            redacted_text = re.sub(pattern, '***', redacted_text)
        return redacted_text
    
    def add_pattern(self, pattern: str) -> None:
        """添加脱敏模式"""
        self.patterns.append(pattern)
```

## 4. 核心实现类

### 4.1 DependencyContainer 实现

```python
class DependencyContainer(IDependencyContainer):
    """依赖注入容器实现"""
    
    def __init__(self):
        self._services = {}
        self._environment = "development"
        self._implementations = {}  # {interface: {env: implementation}}
    
    def register(self, interface: Type, implementation: Type, environment: str = "default") -> None:
        if interface not in self._implementations:
            self._implementations[interface] = {}
        self._implementations[interface][environment] = implementation
    
    def get[T](self, service_type: Type[T]) -> T:
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
```

### 4.2 ConfigSystem 实现

```python
class ConfigSystem(IConfigSystem):
    """配置系统实现"""
    
    def __init__(self, config_loader: IConfigLoader, config_merger: IConfigMerger, config_validator: IConfigValidator):
        self._config_loader = config_loader
        self._config_merger = config_merger
        self._config_validator = config_validator
        self._cache = {}
    
    def load_global_config(self) -> GlobalConfig:
        config_data = self._config_loader.load("configs/global.yaml")
        result = self._config_validator.validate_global_config(config_data)
        if not result.is_valid:
            raise ConfigValidationError(f"Global config validation failed: {result.errors}")
        return GlobalConfig(**config_data)
    
    def load_llm_config(self, name: str) -> LLMConfig:
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
```

### 4.3 Logger 实现

```python
class Logger(ILogger):
    """日志记录器实现"""
    
    def __init__(self, config: GlobalConfig, redactor: LogRedactor):
        self._config = config
        self._redactor = redactor
        self._handlers = []
        self._setup_handlers()
    
    def _setup_handlers(self):
        # 根据配置设置处理器
        for output_config in self._config.log_outputs:
            if output_config["type"] == "console":
                handler = ConsoleHandler(output_config)
            elif output_config["type"] == "file":
                handler = FileHandler(output_config)
            self._handlers.append(handler)
    
    def info(self, message: str, **kwargs) -> None:
        if self._should_log(LogLevel.INFO):
            redacted_message = self._redactor.redact(message, LogLevel.INFO)
            for handler in self._handlers:
                handler.handle(LogLevel.INFO, redacted_message, **kwargs)
    
    def _should_log(self, level: LogLevel) -> bool:
        current_level = LogLevel[self._config.log_level.upper()]
        return level.value >= current_level.value
```

## 5. 配置示例

### 5.1 global.yaml 示例

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

secret_patterns:
  - "sk-[a-zA-Z0-9]{20,}"
  - "\\w+@\\w+\\.\\w+"
  - "1\\d{10}"

env: "development"
debug: true
env_prefix: "AGENT_"
```

### 5.2 llms/_group.yaml 示例

```yaml
# 模型组配置
openai_group:
  base_url: "https://api.openai.com/v1"
  headers:
    User-Agent: "ModularAgent/1.0"
  parameters:
    temperature: 0.7
    max_tokens: 2000

gemini_group:
  base_url: "https://generativelanguage.googleapis.com/v1"
  headers:
    User-Agent: "ModularAgent/1.0"
  parameters:
    temperature: 0.7
```

### 5.3 llms/gpt4.yaml 示例

```yaml
# 个体模型配置
group: "openai_group"
model_type: "openai"
model_name: "gpt-4-turbo"
api_key: "${AGENT_OPENAI_KEY}"
parameters:
  temperature: 0.3  # 覆盖组配置
  top_p: 0.9        # 新增参数
```

## 6. 使用示例

### 6.1 基础使用

```python
# 初始化容器
container = DependencyContainer()
container.register(IConfigLoader, YamlConfigLoader)
container.register(IConfigSystem, ConfigSystem)

# 获取服务
config_system = container.get(IConfigSystem)
global_config = config_system.load_global_config()

# 使用日志
logger = container.get(ILogger)
logger.info("系统启动完成", module="main")
```

### 6.2 配置继承示例

```python
# 加载继承配置
llm_config = config_system.load_llm_config("gpt4")
print(llm_config.base_url)  # 继承自 openai_group
print(llm_config.temperature)  # 覆盖为 0.3
```

这些接口和实现细节为开发团队提供了清晰的指导，确保第一阶段开发的一致性和质量。