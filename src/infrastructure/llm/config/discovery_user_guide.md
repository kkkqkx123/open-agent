# 配置发现器用户指南

## 概述

配置发现器 (`ConfigDiscovery`) 是一个用于自动发现和管理 LLM 客户端配置文件的系统。它支持多环境配置、配置继承和环境变量注入，旨在简化 LLM 配置管理。

## 主要功能

### 1. 配置文件发现

配置发现器会自动扫描指定目录下的 YAML 配置文件：

- 默认配置目录：`configs/llms`
- 递归搜索所有 `.yaml` 文件
- 支持按提供商过滤配置文件
- 按优先级排序配置文件

### 2. 配置加载

- 根据提供商和模型名称加载特定配置
- 支持模型匹配逻辑
- 提供默认配置作为后备选项

### 3. 配置继承

- 支持通过 `inherits_from` 字段实现配置继承
- 自动合并基础配置和覆盖配置
- 支持多层继承关系
- 使用相对路径指定继承的配置文件（相对于配置目录）

### 4. 环境变量注入

- 支持 `${ENV_VAR_NAME:DEFAULT_VALUE}` 格式的环境变量引用
- 递归解析嵌套对象中的环境变量
- 提供默认值机制

### 5. 缓存机制

- 缓存已加载的配置以提高性能
- 提供重新加载功能以支持配置更新

## 配置文件结构

配置文件是标准的 YAML 文件，支持以下字段：

```yaml
# 指定继承的配置文件（可选）
inherits_from: "base_config"  # 建议使用相对路径，指向同目录下的 common.yaml

# 模型列表（可选）
models:
  - "gpt-4"
  - "gpt-3.5-turbo"

# 或者单个模型
model: "gpt-4"

# 优先级（可选，默认为 0）
priority: 10

# LLM 客户端配置参数
base_url: "${OPENAI_BASE_URL:https://api.openai.com/v1}"
api_key: "${OPENAI_API_KEY:sk-...}"
timeout: 30
max_retries: 3
pool_connections: 10
```

## 使用方法

### 初始化配置发现器

```python
from src.infrastructure.llm.config.config_discovery import ConfigDiscovery

# 使用默认配置目录
discovery = ConfigDiscovery()

# 指定自定义配置目录
discovery = ConfigDiscovery(config_dir="custom/config/path")
```

### 发现配置文件

```python
# 发现所有配置文件
all_configs = discovery.discover_configs()

# 发现特定提供商的配置文件
openai_configs = discovery.discover_configs(provider="openai")
```

### 加载特定配置

```python
# 加载特定提供商和模型的配置
config = discovery.load_provider_config(provider="openai", model="gpt-4")
```

### 获取提供商的所有模型

```python
# 获取指定提供商支持的所有模型
models = discovery.get_all_models(provider="openai")
```

### 重新加载配置

```python
# 清除缓存并重新加载所有配置
discovery.reload_configs()
```

## 配置继承机制

配置发现器支持配置继承，允许基础配置被特定配置覆盖：

1. 基础配置文件（如 `base.yaml`）：
```yaml
base_url: "https://api.openai.com/v1"
timeout: 30
max_retries: 3
```

2. 继承配置文件（如 `gpt4_config.yaml`）：
```yaml
inherits_from: "base"  # 使用相对路径，指向同目录下的 base.yaml
model: "gpt-4"
timeout: 60 # 覆盖基础配置中的 timeout
custom_param: "value"  # 添加新参数
```

继承机制会深度合并字典类型的配置项，保留基础配置中未被覆盖的部分。

## 环境变量引用

配置文件支持环境变量引用，格式为 `${VAR_NAME:DEFAULT_VALUE}`：

- `VAR_NAME`：环境变量名称
- `DEFAULT_VALUE`：当环境变量不存在时的默认值（可选）

示例：
```yaml
api_key: "${OPENAI_API_KEY}"  # 无默认值
base_url: "${OPENAI_BASE_URL:https://api.openai.com/v1}"  # 有默认值
```

环境变量解析会递归处理嵌套的对象和数组。

## 优先级排序

配置文件按 `priority` 字段值进行排序（降序），优先级高的配置会优先被匹配：

```yaml
# 高优先级配置
priority: 100
model: "gpt-4"
# ...
```

## 配置匹配逻辑

配置发现器使用以下逻辑来匹配模型和配置：

1. 如果配置文件中明确列出了模型名称，则直接匹配
2. 如果配置文件中没有指定模型列表，则认为是通用配置，可匹配任何模型
3. 按优先级顺序返回第一个匹配的配置

## 默认配置

当未找到匹配的配置时，系统会提供默认配置：

- OpenAI：基础 URL 为 `https://api.openai.com/v1`
- Gemini：基础 URL 为 `https://generativelanguage.googleapis.com/v1`
- Anthropic：基础 URL 为 `https://api.anthropic.com`

## 最佳实践

1. 使用配置继承来避免重复配置
2. 在生产环境中使用环境变量管理敏感信息
3. 为不同环境使用不同的配置文件
4. 合理设置配置优先级以确保正确的配置覆盖

## 故障排除

- 如果配置文件未被发现，请检查文件扩展名是否为 `.yaml`
- 如果环境变量未被解析，请检查格式是否为 `${VAR_NAME:DEFAULT_VALUE}`
- 如果继承配置未生效，请确认基础配置文件存在且路径正确