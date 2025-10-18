# 配置系统使用指南

## 概述

配置系统是 Modular Agent Framework 的核心组件之一，提供了灵活、强大的配置管理功能。它支持配置继承、环境变量注入、热重载、验证和脱敏等特性。

## 核心功能

### 1. 配置加载与继承

配置系统支持分层配置结构，允许组配置和个体配置之间的继承关系：

```yaml
# configs/llms/_group.yaml (组配置)
openai_group:
  base_url: "https://api.openai.com/v1"
  headers:
    User-Agent: "ModularAgent/1.0"
  parameters:
    temperature: 0.7
    max_tokens: 2000

# configs/llms/gpt4.yaml (个体配置)
group: "openai_group"
model_type: "openai"
model_name: "gpt-4"
api_key: "${AGENT_OPENAI_KEY}"
parameters:
  temperature: 0.3  # 覆盖组配置
  top_p: 0.9        # 新增参数
```

### 2. 环境变量注入

支持在配置文件中使用环境变量：

```yaml
api_key: "${AGENT_OPENAI_KEY}"
database_url: "${AGENT_DB_URL:postgresql://localhost/default}"  # 带默认值
```

### 3. 配置验证

使用 Pydantic 模型进行严格的配置验证：

```python
from src.config import ConfigSystem, ConfigValidator

config_system = ConfigSystem(...)
global_config = config_system.load_global_config()  # 自动验证
```

### 4. 热重载

支持配置文件变化时的自动重载：

```python
def config_change_callback(path, config):
    print(f"配置文件变化: {path}")

config_system.watch_for_changes(config_change_callback)
```

### 5. 敏感信息脱敏

自动脱敏日志中的敏感信息：

```python
from src.config.utils import Redactor, LogLevel

redactor = Redactor()
message = "API Key: sk-abc123def456"
redacted = redactor.redact(message, LogLevel.INFO)
# 结果: "API Key: ***"
```

## 使用方法

### 基本使用

```python
from src.config import ConfigSystem, ConfigMerger, ConfigValidator
from src.infrastructure.config_loader import YamlConfigLoader

# 创建组件
config_loader = YamlConfigLoader("configs")
config_merger = ConfigMerger()
config_validator = ConfigValidator()

# 创建配置系统
config_system = ConfigSystem(
    config_loader=config_loader,
    config_merger=config_merger,
    config_validator=config_validator
)

# 加载配置
global_config = config_system.load_global_config()
llm_config = config_system.load_llm_config("gpt4")
agent_config = config_system.load_agent_config("code_agent")
tool_config = config_system.load_tool_config("advanced_tools")
```

### 使用依赖注入容器

```python
from src.infrastructure import DependencyContainer
from src.config import ConfigSystem, ConfigMerger, ConfigValidator

# 创建容器
container = DependencyContainer()

# 注册服务
container.register(ConfigMerger, ConfigMerger)
container.register(ConfigValidator, ConfigValidator)
container.register(ConfigSystem, ConfigSystem)

# 获取服务
config_system = container.get(ConfigSystem)
global_config = config_system.load_global_config()
```

### 配置验证工具

```python
from src.config import ConfigValidatorTool

# 创建验证工具
validator = ConfigValidatorTool("configs")

# 验证所有配置
validator.validate_all()

# 验证特定配置
validator.validate_config("llm", "gpt4")

# 列出配置
validator.list_configs("llms")
```

## 配置结构

### 目录结构

```
configs/
├── global.yaml              # 全局配置
├── llms/                    # LLM配置
│   ├── _group.yaml          # LLM组配置
│   ├── gpt4.yaml            # GPT-4配置
│   └── gemini.yaml          # Gemini配置
├── agents/                  # Agent配置
│   ├── _group.yaml          # Agent组配置
│   └── code_agent.yaml      # 代码Agent配置
└── tool-sets/               # 工具集配置
    ├── _group.yaml          # 工具集组配置
    └── advanced_tools.yaml  # 高级工具配置
```

### 全局配置示例

```yaml
# configs/global.yaml
log_level: "INFO"
log_outputs:
  - type: "console"
    level: "INFO"
    format: "text"
  - type: "file"
    level: "DEBUG"
    format: "json"
    path: "logs/agent.log"

secret_patterns:
  - "sk-[a-zA-Z0-9]{20,}"
  - "\\w+@\\w+\\.\\w+"
  - "1\\d{10}"

env: "development"
debug: true
env_prefix: "AGENT_"

hot_reload: true
watch_interval: 5
```

## 高级功能

### 自定义配置验证

```python
from src.config.config_validator import ConfigValidator

class CustomConfigValidator(ConfigValidator):
    def validate_custom_config(self, config):
        # 自定义验证逻辑
        result = ValidationResult(True)
        
        if "custom_field" not in config:
            result.add_error("缺少必需字段: custom_field")
        
        return result
```

### 自定义脱敏模式

```python
from src.config.utils import Redactor

redactor = Redactor()
redactor.add_pattern("custom_secret", r"custom-[a-zA-Z0-9]+")

message = "Custom secret: custom-abc123"
redacted = redactor.redact(message)
# 结果: "Custom secret: ***"
```

### 配置合并策略

```python
from src.config.config_merger import ConfigMerger

merger = ConfigMerger()

# 深度合并
dict1 = {"a": {"b": 1}, "c": [1, 2]}
dict2 = {"a": {"d": 2}, "c": [3]}
result = merger.deep_merge(dict1, dict2)
# 结果: {"a": {"b": 1, "d": 2}, "c": [1, 2, 3]}

# 按优先级合并
configs = [{"timeout": 30}, {"timeout": 60}, {"retries": 3}]
result = merger.merge_configs_by_priority(configs, ["timeout"])
# 结果: {"timeout": 30, "retries": 3}
```

## 最佳实践

1. **使用组配置**：将公共配置放在组配置中，减少重复
2. **环境变量**：敏感信息使用环境变量注入
3. **配置验证**：充分利用 Pydantic 模型进行验证
4. **热重载**：开发环境启用热重载，生产环境谨慎使用
5. **脱敏处理**：确保日志中不泄露敏感信息

## 故障排除

### 常见问题

1. **配置文件未找到**
   - 检查文件路径是否正确
   - 确认文件扩展名为 `.yaml`

2. **环境变量未找到**
   - 检查环境变量名称是否正确
   - 确认环境变量前缀设置

3. **配置验证失败**
   - 检查配置字段是否符合模型要求
   - 查看详细错误信息

4. **热重载不工作**
   - 检查文件权限
   - 确认监听路径正确

### 调试技巧

1. 使用配置验证工具检查配置
2. 启用调试模式查看详细日志
3. 检查配置继承关系是否正确
4. 验证环境变量是否正确设置

## 性能优化

1. **配置缓存**：配置系统自动缓存已加载的配置
2. **按需加载**：只加载需要的配置
3. **批量操作**：使用批量方法减少重复操作
4. **异步监听**：文件监听使用异步方式，不阻塞主线程

## 扩展开发

### 添加新的配置类型

1. 创建新的配置模型
2. 实现验证方法
3. 添加加载逻辑
4. 编写测试用例

### 自定义配置加载器

```python
from src.infrastructure.config_loader import IConfigLoader

class CustomConfigLoader(IConfigLoader):
    def load(self, config_path):
        # 自定义加载逻辑
        pass
    
    # 实现其他接口方法...
```

## 总结

配置系统提供了完整的配置管理解决方案，支持灵活的配置结构、强大的验证机制和便捷的热重载功能。通过合理使用这些功能，可以大大提高应用程序的可配置性和可维护性。