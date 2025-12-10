# 配置重构快速开始指南

## 概述

本指南帮助开发人员快速理解和使用新的配置系统。

## 核心概念

### 1. 三层架构
- **Impl (实现层)**: 负责配置加载和转换
- **Processor (处理器层)**: 负责配置处理和验证
- **Provider (提供者层)**: 负责配置提供和缓存

### 2. 主要组件
- **ConfigRegistry**: 配置注册中心，管理所有配置组件
- **ConfigFactory**: 配置工厂，创建和配置各种组件
- **ConfigProcessorChain**: 处理器链，串联多个处理器

## 快速使用

### 1. 基本设置

```python
from src.infrastructure.config import ConfigFactory, get_global_registry

# 创建配置工厂
factory = ConfigFactory()

# 获取全局注册中心
registry = get_global_registry()
```

### 2. 设置模块配置

```python
# 设置LLM配置
llm_provider = factory.setup_llm_config()

# 设置Workflow配置
workflow_provider = factory.setup_workflow_config()

# 设置Tools配置
tools_provider = factory.setup_tools_config()

# 设置所有配置
providers = factory.setup_all_configs()
```

### 3. 获取配置

```python
# 获取LLM客户端配置
llm_config = llm_provider.get_client_config("gpt-4")

# 获取LLM模块配置
module_config = llm_provider.get_module_config()

# 获取配置原始数据
raw_config = llm_provider.get_config("gpt-4")

# 获取配置值
value = llm_provider.get_config_value("gpt-4", "temperature", 0.7)
```

### 4. 自定义模块配置

```python
from src.infrastructure.config import BaseConfigImpl, CommonConfigProvider, ConfigSchema

# 创建自定义配置实现
class MyModuleConfigImpl(BaseConfigImpl):
    def transform_config(self, config):
        # 自定义转换逻辑
        return config

# 创建自定义配置模式
class MyModuleSchema(ConfigSchema):
    def __init__(self):
        super().__init__({
            "type": "object",
            "required": ["name", "version"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"}
            }
        })

# 注册自定义模块配置
factory.register_module_config(
    "my_module",
    schema=MyModuleSchema(),
    processor_names=["inheritance", "environment", "validation"],
    cache_enabled=True,
    cache_ttl=300
)

# 获取自定义配置提供者
my_provider = registry.get_provider("my_module")
```

## 迁移现有代码

### 1. 替换配置加载

```python
# 旧方式
from src.core.llm.config import LLMClientConfig
config = LLMClientConfig.from_dict(config_data)

# 新方式
from src.infrastructure.config import get_global_registry
registry = get_global_registry()
llm_provider = registry.get_provider("llm")
config = llm_provider.get_client_config("gpt-4")
```

### 2. 使用适配器保持兼容

```python
# 创建适配器
class LLMConfigAdapter:
    def __init__(self, provider):
        self.provider = provider
    
    def get_config(self, model_name):
        return self.provider.get_client_config(model_name)

# 使用适配器
adapter = LLMConfigAdapter(llm_provider)
config = adapter.get_config("gpt-4")
```

## 常用操作

### 1. 配置缓存管理

```python
# 清除特定配置缓存
provider.clear_cache("gpt-4")

# 清除所有缓存
provider.clear_cache()

# 设置缓存TTL
provider.set_cache_ttl(600)

# 启用/禁用缓存
provider.enable_cache(True)
```

### 2. 配置验证

```python
# 验证配置
is_valid = provider.validate_config("gpt-4")

# 验证配置结构
is_valid = provider.validate_config_structure("gpt-4", ["model_type", "model_name"])
```

### 3. 配置信息查询

```python
# 列出可用配置
configs = provider.list_available_configs()

# 获取配置信息
info = provider.get_config_info("gpt-4")

# 获取提供者统计信息
stats = provider.get_provider_stats()
```

## 处理器使用

### 1. 创建自定义处理器

```python
from src.infrastructure.config.processor import BaseConfigProcessor

class MyProcessor(BaseConfigProcessor):
    def __init__(self):
        super().__init__("my_processor")
    
    def _process_internal(self, config, config_path):
        # 自定义处理逻辑
        return config

# 注册处理器
registry.register_processor("my_processor", MyProcessor())
```

### 2. 创建处理器链

```python
# 创建自定义处理器链
chain = factory.create_processor_chain([
    "inheritance",
    "environment",
    "my_processor",
    "validation"
])
```

## 故障排查

### 1. 常见问题

**问题**: 配置加载失败
```python
# 检查配置文件是否存在
provider.validate_config("config_name")

# 查看详细错误信息
try:
    config = provider.get_config("config_name")
except Exception as e:
    print(f"配置加载失败: {e}")
```

**问题**: 配置缓存问题
```python
# 清除缓存重新加载
provider.clear_cache()
config = provider.get_config("config_name")
```

### 2. 调试技巧

```python
# 启用调试日志
import logging
logging.getLogger("src.infrastructure.config").setLevel(logging.DEBUG)

# 查看注册中心状态
stats = registry.get_registry_stats()
print(stats)

# 验证注册中心完整性
validation = registry.validate_registry()
print(validation)
```

## 最佳实践

1. **使用配置工厂**: 优先使用ConfigFactory创建组件
2. **合理设置缓存**: 根据配置变更频率设置合适的缓存TTL
3. **模块化设计**: 为每个模块创建专门的配置实现
4. **充分测试**: 为自定义配置实现编写单元测试
5. **文档化**: 为自定义配置模式和处理器编写文档

## 更多资源

- [完整重构方案](refactor.md)
- [API文档](../api/config.md)
- [示例代码](../examples/config/)