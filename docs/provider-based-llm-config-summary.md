# Provider-based LLM配置系统重构总结

## 概述

本次重构解决了当前LLM配置中provider与具体llm混在一起导致维护困难的问题，实现了通过provider目录结构配置LLM的新架构，并为API配置添加了缓存支持。

## 主要改进

### 1. Provider-based配置结构

#### 新的目录结构
```
configs/
├── llms/
│   ├── provider/
│   │   ├── openai/
│   │   │   ├── common.yaml          # OpenAI通用配置模板
│   │   │   └── openai-gpt4.yaml     # 具体模型配置
│   │   ├── anthropic/
│   │   │   ├── common.yaml          # Anthropic通用配置模板
│   │   │   └── claude-sonnet.yaml   # 具体模型配置
│   │   └── gemini/
│   │       ├── common.yaml          # Gemini通用配置模板
│   │       └── gemini-pro.yaml      # 具体模型配置
│   ├── _group.yaml                  # 组配置（保持兼容）
│   ├── anthropic-claude.yaml        # 传统配置（保持兼容）
│   └── gemini-pro.yaml              # 传统配置（保持兼容）
```

#### 配置继承机制
- **Provider Common配置**: 包含该provider的所有默认参数、缓存配置、元数据等
- **具体模型配置**: 只需要覆盖与默认值不同的参数，大大简化配置文件
- **向后兼容**: 不在provider目录中的配置文件依然使用旧的解析方式

### 2. 缓存支持

#### 各Provider的缓存支持情况
基于context7 MCP的查询结果：

| Provider | 缓存支持 | 配置设置 |
|----------|----------|----------|
| OpenAI   | 不直接支持API级缓存 | `supports_caching: false` |
| Anthropic | 支持缓存控制 | `supports_caching: true` |
| Gemini   | 明确支持缓存API | `supports_caching: true` |

#### 缓存配置结构
```yaml
# 缓存配置
supports_caching: true
cache_config:
  enabled: true
  ttl_seconds: 3600
  max_size: 1000
  cache_type: "content_cache"  # Gemini特有
```

### 3. 代码修改

#### 配置系统 (`src/config/config_system.py`)
- 新增 `_try_load_provider_config()` 方法支持provider配置加载
- 新增 `_merge_provider_config()` 方法处理配置合并
- 修改 `list_configs()` 方法支持列出provider配置
- 修改 `config_exists()` 方法支持检查provider配置

#### LLM配置模型 (`src/config/models/llm_config.py`)
- 新增 `supports_caching` 字段
- 新增 `cache_config` 字段
- 新增 `provider` 字段
- 新增相关方法：`supports_api_caching()`, `get_cache_ttl()`, `get_cache_max_size()` 等

#### Token计算器 (`src/llm/token_counter.py`)
- 修改 `create_with_model_config()` 方法使用新的缓存配置
- 支持从LLM配置中提取缓存设置并应用到token计算器

## 配置示例

### OpenAI Provider Common配置
```yaml
# configs/llms/provider/openai/common.yaml
provider_type: openai
base_url: "https://api.openai.com/v1"
supports_caching: false  # OpenAI不直接支持API级缓存
cache_config:
  enabled: false
  ttl_seconds: 3600
  max_size: 1000

default_parameters:
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
  max_retries: 3
```

### 具体模型配置（简化版）
```yaml
# configs/llms/provider/openai/openai-gpt4.yaml
model_type: openai
model_name: gpt-4
api_key: "${OPENAI_API_KEY}"
token_counter: openai_gpt4

# 只覆盖需要修改的参数
parameters:
  temperature: 0.7
  max_tokens: 2000

# 继承provider的缓存配置
supports_caching: false
```

## 使用方式

### 1. 创建新的Provider配置
1. 在 `configs/llms/provider/{provider}/` 目录下创建 `common.yaml`
2. 在同目录下创建具体模型配置文件
3. 只需覆盖与默认值不同的参数

### 2. 加载配置
```python
from config.config_system import ConfigSystem

config_system = ConfigSystem(...)
llm_config = config_system.load_llm_config("openai-gpt4")
```

### 3. Token计算器自动使用缓存配置
```python
from llm.token_counter import TokenCounterFactory

token_counter = TokenCounterFactory.create_with_model_config(llm_config.to_dict())
# 缓存配置会自动应用到token计算器
```

## 优势

1. **配置简化**: 具体模型配置文件大大简化，只需覆盖差异化参数
2. **维护性提升**: Provider通用配置集中管理，便于维护和更新
3. **缓存支持**: 明确的缓存配置支持，token计算器能正确使用缓存设置
4. **向后兼容**: 传统配置方式继续支持，平滑迁移
5. **类型安全**: 强类型的配置模型，减少配置错误

## 注意事项

1. **配置优先级**: 具体模型配置 > Provider common配置 > 组配置
2. **缓存设置**: 不同provider的缓存支持能力不同，需根据实际情况配置
3. **路径解析**: 配置系统会自动查找provider目录下的配置文件
4. **验证工具**: 配置验证工具已更新支持provider配置

## 后续工作

1. 完善配置验证工具对provider配置的支持
2. 添加更多provider的common配置模板
3. 优化配置加载性能
4. 添加配置迁移工具